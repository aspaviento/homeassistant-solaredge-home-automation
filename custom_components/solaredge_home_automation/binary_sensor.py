"""Binary sensors for SolarEdge Home Automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SITE_ID, DATA_COORDINATOR, DOMAIN
from .coordinator import SolarEdgeHomeAutomationCoordinator
from .entity import SolarEdgeHomeAutomationEntity


@dataclass(frozen=True, kw_only=True)
class SolarEdgeBinarySensorDescription(BinarySensorEntityDescription):
    """Description for a SolarEdge Home Automation binary sensor."""

    value_fn: Any


SMART_DEVICE_BINARY_SENSORS: tuple[SolarEdgeBinarySensorDescription, ...] = (
    SolarEdgeBinarySensorDescription(
        key="active",
        translation_key="active",
        value_fn=lambda device, info: (device.get("status") or {}).get("level") == 100,
    ),
)

EV_CHARGER_BINARY_SENSORS: tuple[SolarEdgeBinarySensorDescription, ...] = (
    SolarEdgeBinarySensorDescription(
        key="plugged_in",
        translation_key="plugged_in",
        value_fn=lambda device, info: device.get("chargerStatus") == "PLUGGED_IN"
        or bool(device.get("sessionActive")),
    ),
    SolarEdgeBinarySensorDescription(
        key="session_active",
        translation_key="session_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device, info: bool(device.get("sessionActive")),
    ),
    SolarEdgeBinarySensorDescription(
        key="excess_pv_enabled",
        translation_key="excess_pv_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device, info: (
            (info.get("deviceConfigurations") or {}).get("excessPVEnabled") == "ON"
        ),
    ),
    SolarEdgeBinarySensorDescription(
        key="use_battery",
        translation_key="use_battery",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device, info: bool(
            (info.get("deviceConfigurations") or {}).get("useBattery")
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEdge Home Automation binary sensors from a config entry."""
    coordinator: SolarEdgeHomeAutomationCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    site_id = entry.data[CONF_SITE_ID]

    entities = []
    for device in coordinator.data.smart_devices:
        entities.extend(
            SolarEdgeHomeAutomationBinarySensor(coordinator, site_id, device, description)
            for description in SMART_DEVICE_BINARY_SENSORS
        )
    for device in coordinator.data.ev_chargers:
        entities.extend(
            SolarEdgeHomeAutomationBinarySensor(coordinator, site_id, device, description)
            for description in EV_CHARGER_BINARY_SENSORS
        )
    async_add_entities(entities)


class SolarEdgeHomeAutomationBinarySensor(
    SolarEdgeHomeAutomationEntity,
    BinarySensorEntity,
):
    """SolarEdge Home Automation binary sensor."""

    entity_description: SolarEdgeBinarySensorDescription

    def __init__(
        self,
        coordinator: SolarEdgeHomeAutomationCoordinator,
        site_id: str,
        device: dict[str, Any],
        description: SolarEdgeBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(
            coordinator,
            site_id=site_id,
            device=device,
            key=description.key,
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        device = self.current_device
        if device is None:
            return None
        info = self.coordinator.data.ev_charger_info.get(self.device_id, {})
        return bool(self.entity_description.value_fn(device, info))
