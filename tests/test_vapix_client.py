"""Tests for VAPIX async client with mocked HTTP responses."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from e2ectl.vapix.client import VapixClient, VapixError

DEVICE_IP = "10.1.1.10"
BASE_URL = f"http://{DEVICE_IP}"


@pytest.fixture
def mock_aio() -> aioresponses:  # type: ignore[type-arg]
    with aioresponses() as m:
        yield m


# --- Basic device info ---


async def test_get_basic_device_info(mock_aio: aioresponses) -> None:
    payload = {
        "apiVersion": "1.0",
        "data": {
            "propertyList": {
                "ProdShortName": "AXIS P3268-LVE",
                "ProdFullName": "AXIS P3268-LVE Network Camera",
                "SerialNumber": "ACCC8EF12345",
                "Version": "11.8.64",
                "Soc": "ARTPEC-8",
                "ProdNbr": "P3268-LVE",
            }
        },
    }
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        payload=payload,
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.get_basic_device_info()

    assert result["data"]["propertyList"]["ProdShortName"] == "AXIS P3268-LVE"
    assert result["data"]["propertyList"]["SerialNumber"] == "ACCC8EF12345"


# --- Auth failure ---


async def test_auth_failure_raises_vapix_error(mock_aio: aioresponses) -> None:
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        status=401,
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="wrong") as client:
        with pytest.raises(VapixError, match="Authentication failed"):
            await client.get_basic_device_info()


# --- HTTP error ---


async def test_http_error_raises_vapix_error(mock_aio: aioresponses) -> None:
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        status=500,
        body="Internal Server Error",
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        with pytest.raises(VapixError, match="HTTP 500"):
            await client.get_basic_device_info()


# --- Param query ---


async def test_get_param(mock_aio: aioresponses) -> None:
    mock_aio.get(
        f"{BASE_URL}/axis-cgi/param.cgi?action=list&group=Properties.EdgeToEdge",
        body="root.Properties.EdgeToEdge.EdgeToEdge=yes\n",
        content_type="text/plain",
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.get_param("Properties.EdgeToEdge")

    assert "=yes" in result["raw"]


# --- Radar autotracking ---


async def test_radar_autotracking_set_connection(mock_aio: aioresponses) -> None:
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/radar-autotracking.cgi",
        payload={"apiVersion": "1.0", "data": {"connectionStatus": "connected"}},
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.radar_autotracking(
            "setCameraConnection", params={"cameraIp": "10.1.1.20"}
        )

    assert result["data"]["connectionStatus"] == "connected"


async def test_radar_autotracking_get_connection(mock_aio: aioresponses) -> None:
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/radar-autotracking.cgi",
        payload={"apiVersion": "1.0", "data": {"connectionStatus": "connected"}},
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.radar_autotracking("getCameraConnection")

    assert result["data"]["connectionStatus"] == "connected"


# --- Retry on connection error ---


async def test_retry_on_connection_error(mock_aio: aioresponses) -> None:
    # First two attempts fail, third succeeds
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        exception=ConnectionError("Connection refused"),
    )
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        exception=ConnectionError("Connection refused"),
    )
    mock_aio.post(
        f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
        payload={"data": {"propertyList": {"ProdShortName": "AXIS P3268-LVE"}}},
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.get_basic_device_info()

    assert result["data"]["propertyList"]["ProdShortName"] == "AXIS P3268-LVE"


async def test_max_retries_exhausted(mock_aio: aioresponses) -> None:
    # All 3 attempts fail
    for _ in range(3):
        mock_aio.post(
            f"{BASE_URL}/axis-cgi/basicdeviceinfo.cgi",
            exception=ConnectionError("Connection refused"),
        )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        with pytest.raises(VapixError, match="Failed to reach"):
            await client.get_basic_device_info()


# --- Plain text response ---


async def test_plain_text_response(mock_aio: aioresponses) -> None:
    mock_aio.get(
        f"{BASE_URL}/axis-cgi/param.cgi?action=list&group=Properties.Audio",
        body="root.Properties.Audio.Audio=yes\nroot.Properties.Audio.Duplex=half\n",
        content_type="text/plain",
    )

    async with VapixClient(ip=DEVICE_IP, username="root", password="pass") as client:
        result = await client.get_param("Properties.Audio")

    assert "Audio=yes" in result["raw"]


# --- Context manager ---


async def test_context_manager_closes_session() -> None:
    client = VapixClient(ip=DEVICE_IP, username="root", password="pass")
    async with client:
        session = await client._get_session()
        assert not session.closed
    assert client._session is not None
    assert client._session.closed
