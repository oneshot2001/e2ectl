"""Device models — types and info returned from discovery."""

from enum import StrEnum

from pydantic import BaseModel


class DeviceType(StrEnum):
    CAMERA = "camera"
    SPEAKER = "speaker"
    RADAR = "radar"
    MICROPHONE = "mic"
    INTERCOM = "intercom"
    STROBE = "strobe"
    UNKNOWN = "unknown"


class DeviceInfo(BaseModel):
    """A discovered Axis device with its capabilities."""

    ip: str
    model: str
    full_name: str
    serial: str
    firmware: str
    soc: str
    device_type: DeviceType = DeviceType.UNKNOWN
    e2e_supported: bool = False
    e2e_capabilities: list[str] = []
    active_pairings: list[dict[str, str]] = []

    @property
    def address(self) -> str:
        return self.ip
