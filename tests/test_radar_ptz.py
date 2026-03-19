"""Tests for radar-PTZ pairing module with mocked VAPIX responses."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from e2ectl.models.pairing import PairingState
from e2ectl.pairing import radar_ptz
from e2ectl.vapix.client import VapixClient

RADAR_IP = "10.1.1.30"
BASE_URL = f"http://{RADAR_IP}"
AUTOTRACK_URL = f"{BASE_URL}/axis-cgi/radar-autotracking.cgi"


@pytest.fixture
def mock_aio() -> aioresponses:  # type: ignore[type-arg]
    with aioresponses() as m:
        yield m


async def test_set_camera_connection(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        result = await radar_ptz.set_camera_connection(client, "10.1.1.20")

    assert "data" in result


async def test_get_camera_connection_connected(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {"connectionStatus": "connected"}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        state = await radar_ptz.get_camera_connection(client)

    assert state == PairingState.CONNECTED


async def test_get_camera_connection_disconnected(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {"connectionStatus": "disconnected"}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        state = await radar_ptz.get_camera_connection(client)

    assert state == PairingState.DISCONNECTED


async def test_get_camera_connection_unknown_status(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {"connectionStatus": "weird_state"}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        state = await radar_ptz.get_camera_connection(client)

    assert state == PairingState.UNKNOWN


async def test_get_camera_connection_error_returns_unknown(
    mock_aio: aioresponses,
) -> None:
    mock_aio.post(AUTOTRACK_URL, status=500, body="Internal error")

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        state = await radar_ptz.get_camera_connection(client)

    assert state == PairingState.UNKNOWN


async def test_set_mounting_height(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        result = await radar_ptz.set_camera_mounting_height(client, 3.5)

    assert "data" in result


async def test_set_pan_offset(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        result = await radar_ptz.set_camera_pan_offset(client, 15.0)

    assert "data" in result


async def test_set_tracking(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        result = await radar_ptz.set_tracking(client, enabled=True)

    assert "data" in result


async def test_disconnect(mock_aio: aioresponses) -> None:
    mock_aio.post(
        AUTOTRACK_URL,
        payload={"apiVersion": "1.0", "data": {}},
    )

    async with VapixClient(ip=RADAR_IP, username="root", password="pass") as client:
        result = await radar_ptz.disconnect(client)

    assert "data" in result
