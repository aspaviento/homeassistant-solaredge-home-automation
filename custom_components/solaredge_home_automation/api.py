"""SolarEdge Home Automation API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from solaredge_web import SolarEdgeWeb


class SolarEdgeHomeAutomationApiError(Exception):
    """Base error for SolarEdge Home Automation API failures."""


class SolarEdgeHomeAutomationAuthError(SolarEdgeHomeAutomationApiError):
    """Raised when SolarEdge authentication fails."""


@dataclass(frozen=True)
class SolarEdgeHomeAutomationDevice:
    """Normalized SolarEdge Home Automation device."""

    device_id: str
    name: str
    device_type: str
    raw: dict[str, Any]


class SolarEdgeHomeAutomationClient:
    """Client for SolarEdge Home Automation endpoints."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        site_id: str,
        session: aiohttp.ClientSession,
        timeout: int = 10,
    ) -> None:
        """Initialize the client."""
        self.site_id = site_id
        self._web = SolarEdgeWeb(
            username=username,
            password=password,
            site_id=site_id,
            session=session,
            timeout=timeout,
        )
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def async_get_site_devices(self) -> dict[str, Any]:
        """Return the raw SolarEdge Home Automation site devices payload."""
        return await self._request_json(
            "GET",
            f"https://monitoring.solaredge.com/services/api/homeautomation/v1.0/sites/{self.site_id}/devices",
        )

    async def async_get_ev_charger_info(self, device_id: str) -> dict[str, Any]:
        """Return the raw EV Charger info payload."""
        return await self._request_json(
            "GET",
            f"https://monitoring.solaredge.com/services/m/so/ev-charger/site/{self.site_id}/device/{device_id}/info",
        )

    async def async_set_activation_state(
        self,
        device_id: str,
        *,
        mode: str,
        level: int,
        duration: int | None = None,
    ) -> dict[str, Any]:
        """Set a device activation state."""
        return await self._request_json(
            "PUT",
            f"https://monitoring.solaredge.com/services/m/api/homeautomation/v1.0/{self.site_id}/devices/{device_id}/activationState",
            json={"mode": mode, "level": level, "duration": duration},
        )

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run an authenticated request and return JSON."""
        await self._web.async_login()
        headers = dict(getattr(self._web, "_auth_headers", {}))
        headers["Accept"] = "application/json"
        if json is not None:
            headers["Content-Type"] = "application/json"
            csrf_token = self._find_cookie_value("CSRF-TOKEN")
            if csrf_token:
                headers["X-CSRF-TOKEN"] = csrf_token

        try:
            response = await self._web.session.request(
                method,
                url,
                headers=headers,
                json=json,
                timeout=self._timeout,
            )
            if response.status in (401, 403):
                raise SolarEdgeHomeAutomationAuthError(
                    f"SolarEdge rejected the request with HTTP {response.status}"
                )
            response.raise_for_status()
            payload = await response.json()
        except SolarEdgeHomeAutomationAuthError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SolarEdgeHomeAutomationApiError(str(err)) from err

        status = payload.get("status")
        http_status = payload.get("httpStatus")
        if status and status != "PASSED":
            raise SolarEdgeHomeAutomationApiError(
                f"SolarEdge returned status {status}: {payload.get('errorMessages')}"
            )
        if http_status and int(http_status) >= 400:
            raise SolarEdgeHomeAutomationApiError(
                f"SolarEdge returned HTTP status {http_status}: {payload.get('errorMessages')}"
            )
        return payload

    def _find_cookie_value(self, name: str) -> str | None:
        """Return a SolarEdge web session cookie value."""
        find_cookie = getattr(self._web, "_find_cookie", None)
        if find_cookie is None:
            return None
        cookie = find_cookie(name)
        if cookie is None:
            return None
        return str(cookie.value)
