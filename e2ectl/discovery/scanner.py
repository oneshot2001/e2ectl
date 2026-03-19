"""Async subnet scanner — wraps axelib scanner with e2ectl DeviceInfo."""

from __future__ import annotations

from axelib.discovery.scanner import scan_subnet as _base_scan_subnet

from e2ectl.models.device import DeviceInfo


async def scan_subnet(
    cidr: str,
    username: str = "root",
    password: str = "",
    timeout: int = 5,
    verbose: bool = False,
) -> list[DeviceInfo]:
    """Scan a CIDR range for Axis devices.

    Wraps axelib's scan_subnet and converts base DeviceInfo to e2ectl's
    subclass with e2e fields.

    Args:
        cidr: Network in CIDR notation, e.g. "10.1.1.0/24".
        username: Default username for device auth.
        password: Default password for device auth.
        timeout: Per-device timeout in seconds.
        verbose: Enable verbose logging.

    Returns:
        List of discovered e2ectl DeviceInfo objects, sorted by IP.
    """
    base_devices = await _base_scan_subnet(
        cidr=cidr,
        username=username,
        password=password,
        timeout=timeout,
        verbose=verbose,
    )

    # Convert base DeviceInfo to e2ectl's DeviceInfo subclass
    return [
        DeviceInfo(**d.model_dump())
        for d in base_devices
    ]
