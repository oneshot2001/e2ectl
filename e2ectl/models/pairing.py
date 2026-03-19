"""Pairing models — types, states, and specs."""

from enum import StrEnum

from pydantic import BaseModel


class PairingType(StrEnum):
    AUDIO = "audio"
    RADAR_PTZ = "radar-ptz"
    CAMERA = "camera"


class PairingState(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECT_FAILED = "connect_failed"
    UNKNOWN = "unknown"


class PairingSpec(BaseModel):
    """A declared pairing from a manifest."""

    name: str
    type: PairingType
    subtype: str | None = None
    primary: str
    secondary: str
    config: dict[str, str | int | float | bool] | None = None
    labels: dict[str, str] = {}
