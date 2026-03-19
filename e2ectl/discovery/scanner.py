"""Async subnet scanner — discovers Axis devices via basicdeviceinfo.cgi."""

from __future__ import annotations

import asyncio
import ipaddress
import logging

from e2ectl.discovery.classifier import classify_device
from e2ectl.models.device import DeviceInfo
from e2ectl.vapix.client import VapixClient, VapixError

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 50


async def _probe_device(
    ip: str,
    username: str,
    password: str,
    timeout: int,
    verbose: bool,
) -> DeviceInfo | None:
    """Probe a single IP for an Axis device."""
    try:
        async with VapixClient(
            ip=ip, username=username, password=password, timeout=timeout, verbose=verbose
        ) as client:
            resp = await client.get_basic_device_info()

        props = resp.get("data", {}).get("propertyList", {})
        if not props:
            return None

        model = props.get("ProdShortName", props.get("ProdNbr", ""))
        return DeviceInfo(
            ip=ip,
            model=model,
            full_name=props.get("ProdFullName", model),
            serial=props.get("SerialNumber", ""),
            firmware=props.get("Version", ""),
            soc=props.get("Soc", ""),
            device_type=classify_device(model),
        )

    except VapixError:
        return None
    except Exception:
        if verbose:
            logger.debug("Probe failed for %s", ip, exc_info=True)
        return None


async def scan_subnet(
    cidr: str,
    username: str = "root",
    password: str = "",
    timeout: int = 5,
    verbose: bool = False,
) -> list[DeviceInfo]:
    """Scan a CIDR range for Axis devices.

    Args:
        cidr: Network in CIDR notation, e.g. "10.1.1.0/24".
        username: Default username for device auth.
        password: Default password for device auth.
        timeout: Per-device timeout in seconds.
        verbose: Enable verbose logging.

    Returns:
        List of discovered DeviceInfo objects, sorted by IP.
    """
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(ip) for ip in network.hosts()]

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def bounded_probe(ip: str) -> DeviceInfo | None:
        async with sem:
            return await _probe_device(ip, username, password, timeout, verbose)

    results = await asyncio.gather(*[bounded_probe(ip) for ip in hosts])
    devices = [d for d in results if d is not None]
    devices.sort(key=lambda d: ipaddress.ip_address(str(d.ip)))
    return devices
