"""Pairing engine — orchestrates pairing operations from a manifest."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from e2ectl.models.pairing import PairingState, PairingType
from e2ectl.pairing import radar_ptz
from e2ectl.vapix.client import VapixClient, VapixError

if TYPE_CHECKING:
    from e2ectl.models.manifest import ManifestDevice, SitePairing

logger = logging.getLogger(__name__)


@dataclass
class PairingResult:
    name: str
    pairing_type: str
    primary: str
    secondary: str
    success: bool = False
    state: PairingState = PairingState.UNKNOWN
    error: str = ""


@dataclass
class ApplyResult:
    results: list[PairingResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def exit_code(self) -> int:
        if self.failed == 0:
            return 0
        if self.succeeded > 0:
            return 1  # partial failure
        return 2  # total failure


class PairingEngine:
    """Orchestrates pairing operations from a validated manifest."""

    def __init__(
        self,
        manifest: SitePairing,
        verbose: bool = False,
    ) -> None:
        self.manifest = manifest
        self.verbose = verbose
        self._devices: dict[str, ManifestDevice] = {d.name: d for d in manifest.devices}

    def _get_credentials(self, device: ManifestDevice) -> tuple[str, str]:
        if device.credentials:
            return device.credentials.username, device.credentials.password
        return (
            self.manifest.defaults.credentials.username,
            self.manifest.defaults.credentials.password,
        )

    def _client_for(self, device: ManifestDevice) -> VapixClient:
        username, password = self._get_credentials(device)
        return VapixClient(
            ip=device.ip,
            username=username,
            password=password,
            timeout=self.manifest.defaults.timeout,
            verbose=self.verbose,
        )

    async def apply(self) -> ApplyResult:
        """Execute all pairings in the manifest. Continues on failure."""
        result = ApplyResult()

        for pairing in self.manifest.pairings:
            primary = self._devices[pairing.primary]
            secondary = self._devices[pairing.secondary]

            pr = PairingResult(
                name=pairing.name,
                pairing_type=pairing.type,
                primary=primary.ip,
                secondary=secondary.ip,
            )

            try:
                if pairing.type == PairingType.RADAR_PTZ:
                    async with self._client_for(primary) as client:
                        await radar_ptz.set_camera_connection(client, secondary.ip)

                        # Apply optional config
                        if pairing.config:
                            if "mountingHeight" in pairing.config:
                                await radar_ptz.set_camera_mounting_height(
                                    client, float(pairing.config["mountingHeight"])
                                )
                            if "panOffset" in pairing.config:
                                await radar_ptz.set_camera_pan_offset(
                                    client, float(pairing.config["panOffset"])
                                )
                            if "tracking" in pairing.config:
                                await radar_ptz.set_tracking(
                                    client, bool(pairing.config["tracking"])
                                )

                        pr.state = await radar_ptz.get_camera_connection(client)
                        pr.success = True

                elif pairing.type == PairingType.AUDIO:
                    pr.success = False
                    pr.error = "Audio pairing not yet implemented"

                elif pairing.type == PairingType.CAMERA:
                    pr.success = False
                    pr.error = "Camera pairing not yet implemented"

                else:
                    pr.success = False
                    pr.error = f"Unknown pairing type: {pairing.type}"

            except VapixError as e:
                pr.success = False
                pr.error = str(e)
                logger.error("Pairing '%s' failed: %s", pairing.name, e)

            result.results.append(pr)

        return result

    async def teardown(self) -> ApplyResult:
        """Remove all pairings declared in the manifest."""
        result = ApplyResult()

        for pairing in self.manifest.pairings:
            primary = self._devices[pairing.primary]
            secondary = self._devices[pairing.secondary]

            pr = PairingResult(
                name=pairing.name,
                pairing_type=pairing.type,
                primary=primary.ip,
                secondary=secondary.ip,
            )

            try:
                if pairing.type == PairingType.RADAR_PTZ:
                    async with self._client_for(primary) as client:
                        await radar_ptz.disconnect(client)
                        pr.state = PairingState.DISCONNECTED
                        pr.success = True
                else:
                    pr.success = False
                    pr.error = f"Teardown not implemented for type: {pairing.type}"

            except VapixError as e:
                pr.success = False
                pr.error = str(e)

            result.results.append(pr)

        return result
