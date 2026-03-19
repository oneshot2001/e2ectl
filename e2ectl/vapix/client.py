"""e2ectl VAPIX client — extends axelib base with pairing-specific methods."""

from __future__ import annotations

import json
from typing import Any

from axelib.vapix.client import VapixClient as _BaseVapixClient
from axelib.vapix.client import VapixError  # noqa: F401

__all__ = ["VapixClient", "VapixError"]


class VapixClient(_BaseVapixClient):
    """Async VAPIX client with e2ectl-specific pairing methods.

    Inherits base VAPIX functionality (Digest auth, retries, GET/POST)
    from axelib and adds get_param() and radar_autotracking().
    """

    async def __aenter__(self) -> VapixClient:
        return self

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

        return await self.post(
            "/axis-cgi/radar-autotracking.cgi",
            data=json.dumps(body),
        )
