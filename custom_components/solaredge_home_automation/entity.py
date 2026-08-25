"""Shared entity helpers for SolarEdge Home Automation."""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SITE_ID, DOMAIN, EV_CHARGER
from .coordinator import SolarEdgeHomeAutomationCoordinator


class SolarEdgeHomeAutomationEntity(CoordinatorEntity[SolarEdgeHomeAutomationCoordinator]):
    """Base SolarEdge Home Automation entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEdgeHomeAutomationCoordinator,
        *,
        site_id: str,
        device: dict[str, Any],
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.site_id = site_id
        self.device_id = str(device.get("reporterId") or device.get("deviceId"))
        self.device_type = str(device.get("type") or "device")
        self._attr_unique_id = f"{site_id}_{self.device_id}_{key}"
        self._attr_device_info = _device_info(site_id, device)

    @property
    def current_device(self) -> dict[str, Any] | None:
        """Return the current raw device payload."""
        data = self.coordinator.data
        if data is None:
            return None

        candidates = data.ev_chargers if self.device_type == EV_CHARGER else data.smart_devices
        for device in candidates:
            if str(device.get("reporterId") or device.get("deviceId")) == self.device_id:
                return device
        return None


def _device_info(site_id: str, device: dict[str, Any]) -> DeviceInfo:
    """Build Home Assistant device info."""
    device_id = str(device.get("reporterId") or device.get("deviceId"))
    identifiers = {(DOMAIN, site_id, device_id)}

    return DeviceInfo(
        identifiers=identifiers,
        manufacturer=str(device.get("manufacturer") or "SolarEdge"),
        model=str(device.get("model") or device.get("type") or "Device"),
        name=str(device.get("name") or device.get(CONF_NAME) or device_id),
        sw_version=device.get("swVersion"),
        via_device=(DOMAIN, site_id),
    )
