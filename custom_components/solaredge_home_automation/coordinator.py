"""Data coordinator for SolarEdge Home Automation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolarEdgeHomeAutomationApiError, SolarEdgeHomeAutomationClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SITE_ID,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_TIMER_DURATION_MINUTES,
    DOMAIN,
    EV_CHARGER,
    LOGGER,
)

EV_STATUS_REFRESH_OFFSETS = (5, 15, 30, 50)


@dataclass(frozen=True)
class SolarEdgeHomeAutomationData:
    """Normalized coordinator data."""

    raw: dict[str, Any]
    smart_devices: list[dict[str, Any]]
    ev_chargers: list[dict[str, Any]]
    ev_charger_info: dict[str, dict[str, Any]]


class SolarEdgeHomeAutomationCoordinator(
    DataUpdateCoordinator[SolarEdgeHomeAutomationData]
):
    """Coordinate SolarEdge Home Automation data updates."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
        )
        self.client = SolarEdgeHomeAutomationClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            site_id=entry.data[CONF_SITE_ID],
            session=async_get_clientsession(hass),
        )
        self.timer_duration_minutes: dict[str, int] = {}
        self._ev_command_lock = asyncio.Lock()
        self._ev_refresh_tasks: dict[str, asyncio.Task[None]] = {}

    async def _async_update_data(self) -> SolarEdgeHomeAutomationData:
        """Fetch and normalize SolarEdge Home Automation data."""
        try:
            raw = await self.client.async_get_site_devices()
        except (SolarEdgeHomeAutomationApiError, ClientError, TimeoutError) as err:
            raise UpdateFailed(str(err)) from err

        smart_devices = list(raw.get("devices") or [])
        ev_chargers = list((raw.get("devicesByType") or {}).get(EV_CHARGER) or [])

        ev_charger_info = {}
        for charger in ev_chargers:
            device_id = str(charger.get("reporterId") or charger.get("deviceId") or "")
            if not device_id:
                continue
            try:
                ev_charger_info[device_id] = await self.client.async_get_ev_charger_info(
                    device_id
                )
            except SolarEdgeHomeAutomationApiError as err:
                LOGGER.debug("Could not fetch EV Charger info for %s: %s", device_id, err)

        return SolarEdgeHomeAutomationData(
            raw=raw,
            smart_devices=smart_devices,
            ev_chargers=ev_chargers,
            ev_charger_info=ev_charger_info,
        )

    async def async_charge_now(self, device_id: str) -> None:
        """Start EV charging now."""
        await self._async_set_ev_charging(device_id, level=100, expected="CHARGING")

    async def async_stop_charging(self, device_id: str) -> None:
        """Stop EV charging."""
        await self._async_set_ev_charging(device_id, level=0, expected="CONNECTED")

    async def _async_set_ev_charging(
        self, device_id: str, *, level: int, expected: str
    ) -> None:
        """Send one command and follow up if the charger has not confirmed it."""
        async with self._ev_command_lock:
            if previous := self._ev_refresh_tasks.pop(device_id, None):
                previous.cancel()

            await self.client.async_set_activation_state(
                device_id, mode="MANUAL", level=level
            )
            started = asyncio.get_running_loop().time()
            previous_data = self.data
            await self.async_request_refresh()
            if not self._ev_status_matches(device_id, expected, previous_data):
                self._ev_refresh_tasks[device_id] = (
                    self.config_entry.async_create_background_task(
                        self.hass,
                        self._async_follow_ev_status(
                            device_id, expected, started, previous_data
                        ),
                        name="SolarEdge EV charger status follow-up",
                    )
                )

    def _ev_status_matches(
        self,
        device_id: str,
        expected: str,
        previous_data: SolarEdgeHomeAutomationData | None,
    ) -> bool:
        """Check fresh data for the same status field that backs the sensor."""
        return (
            self.last_update_success
            and self.data is not None
            and self.data is not previous_data
            and any(
                str(charger.get("reporterId") or charger.get("deviceId") or "") == device_id
                and charger.get("connectionStatus") == expected
                for charger in self.data.ev_chargers
            )
        )

    async def _async_follow_ev_status(
        self,
        device_id: str,
        expected: str,
        started: float,
        previous_data: SolarEdgeHomeAutomationData | None,
    ) -> None:
        """Request bounded refreshes without replaying the charger command."""
        loop = asyncio.get_running_loop()
        try:
            for offset in EV_STATUS_REFRESH_OFFSETS:
                delay = started + offset - loop.time()
                if delay <= 0:
                    continue
                await asyncio.sleep(delay)
                if self._ev_status_matches(device_id, expected, previous_data):
                    return
                await self.async_request_refresh()
                if self._ev_status_matches(device_id, expected, previous_data):
                    return
        finally:
            if self._ev_refresh_tasks.get(device_id) is asyncio.current_task():
                self._ev_refresh_tasks.pop(device_id)

    async def async_turn_on_device(self, device_id: str) -> None:
        """Turn on a Smart Energy device manually."""
        await self.client.async_set_activation_state(
            device_id,
            mode="MANUAL",
            level=100,
        )
        await self.async_request_refresh()

    async def async_turn_off_device(self, device_id: str) -> None:
        """Turn off a Smart Energy device manually."""
        await self.client.async_set_activation_state(
            device_id,
            mode="MANUAL",
            level=0,
        )
        await self.async_request_refresh()

    async def async_auto_device(self, device_id: str) -> None:
        """Return a Smart Energy device to automatic operation."""
        await self.client.async_set_activation_state(
            device_id,
            mode="AUTO",
            level=None,
        )
        await self.async_request_refresh()

    async def async_turn_on_device_for(self, device_id: str, duration: int) -> None:
        """Turn on a Smart Energy device manually for a duration in minutes."""
        await self.client.async_set_activation_state(
            device_id,
            mode="MANUAL",
            level=100,
            duration=duration,
        )
        await self.async_request_refresh()

    async def async_turn_on_device_for_selected_duration(self, device_id: str) -> None:
        """Turn on a Smart Energy device for its selected timer duration."""
        await self.async_turn_on_device_for(
            device_id,
            self.timer_duration_minutes.get(device_id, DEFAULT_TIMER_DURATION_MINUTES),
        )

    def set_timer_duration(self, device_id: str, duration: int) -> None:
        """Set the selected timer duration for a Smart Energy device."""
        self.timer_duration_minutes[device_id] = duration
