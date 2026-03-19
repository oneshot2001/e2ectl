"""Radar-PTZ pairing via /axis-cgi/radar-autotracking.cgi."""

from __future__ import annotations

from typing import Any

from e2ectl.models.pairing import PairingState
from e2ectl.vapix.client import VapixClient, VapixError


async def set_camera_connection(
    client: VapixClient,
    camera_ip: str,
) -> dict[str, Any]:
    """Establish a radar → camera pairing."""
    return await client.radar_autotracking(
        "setCameraConnection",
        params={"cameraIp": camera_ip},
    )


async def get_camera_connection(client: VapixClient) -> PairingState:
    """Query the current radar → camera pairing state."""
    try:
        resp = await client.radar_autotracking("getCameraConnection")
        data = resp.get("data", {})
        state_str = data.get("connectionStatus", "unknown")
        try:
            return PairingState(state_str)
        except ValueError:
            return PairingState.UNKNOWN
    except VapixError:
        return PairingState.UNKNOWN


async def set_camera_mounting_height(
    client: VapixClient,
    height: float,
) -> dict[str, Any]:
    """Set the camera mounting height on the radar."""
    return await client.radar_autotracking(
        "setCameraMountingHeight",
        params={"height": height},
    )


async def set_camera_pan_offset(
    client: VapixClient,
    offset: float,
) -> dict[str, Any]:
    """Set the camera pan offset on the radar."""
    return await client.radar_autotracking(
        "setCameraPanOffset",
        params={"offset": offset},
    )


async def set_tracking(
    client: VapixClient,
    enabled: bool,
) -> dict[str, Any]:
    """Enable or disable autotracking."""
    return await client.radar_autotracking(
        "setTracking",
        params={"enabled": enabled},
    )


async def disconnect(client: VapixClient) -> dict[str, Any]:
    """Disconnect radar → camera pairing by setting empty IP."""
    return await client.radar_autotracking(
        "setCameraConnection",
        params={"cameraIp": ""},
    )
