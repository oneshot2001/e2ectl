"""E2E capability profiler — queries device properties for pairing support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from e2ectl.vapix.client import VapixClient, VapixError

if TYPE_CHECKING:
    from e2ectl.models.device import DeviceInfo

logger = logging.getLogger(__name__)


async def profile_e2e_capabilities(
    device: DeviceInfo,
    username: str = "root",
    password: str = "",
    timeout: int = 10,
) -> DeviceInfo:
    """Query a device for its edge-to-edge capabilities.

    Updates the device's e2e_supported and e2e_capabilities fields in-place
    and returns the updated device.
    """
    capabilities: list[str] = []

    async with VapixClient(
        ip=device.address, username=username, password=password, timeout=timeout
    ) as client:
        # Check Properties.EdgeToEdge
        try:
            resp = await client.get_param("Properties.EdgeToEdge")
            raw = resp.get("raw", "")
            if "=yes" in raw.lower():
                capabilities.append("e2e")
        except VapixError:
            logger.debug("No E2E properties on %s", device.address)

        # Check Properties.Audio
        try:
            resp = await client.get_param("Properties.Audio")
            raw = resp.get("raw", "")
            if "=yes" in raw.lower():
                capabilities.append("audio")
        except VapixError:
            logger.debug("No audio properties on %s", device.address)

        # Check Properties.PTZ
        try:
            resp = await client.get_param("Properties.PTZ")
            raw = resp.get("raw", "")
            if "=yes" in raw.lower():
                capabilities.append("ptz")
        except VapixError:
            logger.debug("No PTZ properties on %s", device.address)

    device.e2e_supported = "e2e" in capabilities
    device.e2e_capabilities = capabilities
    return device
