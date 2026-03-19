"""Async VAPIX HTTP client with Digest auth and retry logic."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_BASE = 1.0


class VapixError(Exception):
    """VAPIX API error with human-readable message."""

    def __init__(self, message: str, status: int | None = None, device_ip: str = ""):
        self.status = status
        self.device_ip = device_ip
        super().__init__(message)


class VapixClient:
    """Async HTTP client for Axis VAPIX APIs.

    Handles Digest authentication, retries with exponential backoff,
    and base URL construction from device IP.
    """

    def __init__(
        self,
        ip: str,
        username: str = "root",
        password: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        verbose: bool = False,
    ) -> None:
        self.ip = ip
        self.base_url = f"http://{ip}"
        self._auth = aiohttp.DigestAuth(username, password)  # type: ignore[operator]
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._verbose = verbose
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> VapixClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """GET request with retry logic."""
        return await self._request("GET", path, params=params)

    async def post(
        self, path: str, data: dict[str, Any] | str | None = None
    ) -> dict[str, Any]:
        """POST request with retry logic."""
        return await self._request("POST", path, data=data)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: dict[str, Any] | str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        session = await self._get_session()
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self._verbose:
                    logger.info("[%s] %s %s (attempt %d)", self.ip, method, path, attempt)

                kwargs: dict[str, Any] = {"auth": self._auth}
                if params:
                    kwargs["params"] = params
                if data:
                    kwargs["data"] = data

                async with session.request(method, url, **kwargs) as resp:
                    if self._verbose:
                        logger.info("[%s] Response: %d", self.ip, resp.status)

                    if resp.status == 401:
                        raise VapixError(
                            f"Authentication failed for {self.ip} — check username/password",
                            status=401,
                            device_ip=self.ip,
                        )

                    if resp.status >= 400:
                        body = await resp.text()
                        raise VapixError(
                            f"VAPIX error from {self.ip}: HTTP {resp.status} — {body[:200]}",
                            status=resp.status,
                            device_ip=self.ip,
                        )

                    content_type = resp.headers.get("Content-Type", "")
                    if "json" in content_type or "javascript" in content_type:
                        result: dict[str, Any] = await resp.json(content_type=None)
                        return result

                    text = await resp.text()
                    return {"raw": text}

            except VapixError:
                raise
            except (TimeoutError, aiohttp.ClientError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = BACKOFF_BASE * (2 ** (attempt - 1))
                    if self._verbose:
                        logger.warning(
                            "[%s] Request failed (%s), retrying in %.1fs...",
                            self.ip,
                            type(e).__name__,
                            wait,
                        )
                    await asyncio.sleep(wait)

        raise VapixError(
            f"Failed to reach {self.ip} after {MAX_RETRIES} attempts: {last_error}",
            device_ip=self.ip,
        )

    async def get_basic_device_info(self) -> dict[str, Any]:
        """Query /axis-cgi/basicdeviceinfo.cgi for all device properties."""
        return await self.post(
            "/axis-cgi/basicdeviceinfo.cgi",
            data='{"apiVersion": "1.0", "method": "getAllProperties"}',
        )

    async def get_param(self, group: str) -> dict[str, Any]:
        """Query /axis-cgi/param.cgi for a parameter group."""
        return await self.get(
            "/axis-cgi/param.cgi",
            params={"action": "list", "group": group},
        )

    async def radar_autotracking(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Call /axis-cgi/radar-autotracking.cgi with a JSON-RPC style body."""
        body: dict[str, Any] = {
            "apiVersion": "1.0",
            "method": method,
        }
        if params:
            body["params"] = params
        import json

        return await self.post(
            "/axis-cgi/radar-autotracking.cgi",
            data=json.dumps(body),
        )
