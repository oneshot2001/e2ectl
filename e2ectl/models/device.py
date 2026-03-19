"""Device models — e2ectl extension with edge-to-edge fields."""

from axelib.models.device import DeviceInfo as _BaseDeviceInfo
from axelib.models.device import DeviceType  # noqa: F401

__all__ = ["DeviceInfo", "DeviceType"]


class DeviceInfo(_BaseDeviceInfo):
    """A discovered Axis device with e2ectl pairing capabilities."""

    e2e_supported: bool = False
    e2e_capabilities: list[str] = []
    active_pairings: list[dict[str, str]] = []
