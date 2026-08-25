"""Sensors for SolarEdge Home Automation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SITE_ID, DATA_COORDINATOR, DOMAIN
from .coordinator import SolarEdgeHomeAutomationCoordinator
from .entity import SolarEdgeHomeAutomationEntity


@dataclass(frozen=True, kw_only=True)
class SolarEdgeSensorDescription(SensorEntityDescription):
    """Description for a SolarEdge Home Automation sensor."""

    value_fn: Any
    attributes_fn: Any | None = None


SMART_DEVICE_SENSORS: tuple[SolarEdgeSensorDescription, ...] = (
    SolarEdgeSensorDescription(
        key="active_power",
        translation_key="active_power",
        value_fn=lambda device, info: (device.get("status") or {}).get("activePowerMeter"),
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="activation_mode",
        translation_key="activation_mode",
        value_fn=lambda device, info: device.get("activationMode"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="schedule_type",
        translation_key="schedule_type",
        value_fn=lambda device, info: (device.get("status") or {}).get("scheduleType"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

EV_CHARGER_SENSORS: tuple[SolarEdgeSensorDescription, ...] = (
    SolarEdgeSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        value_fn=lambda device, info: _wh_to_kwh(device.get("sessionEnergy")),
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
    SolarEdgeSensorDescription(
        key="session_duration",
        translation_key="session_duration",
        value_fn=lambda device, info: device.get("sessionDuration"),
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="session_distance",
        translation_key="session_distance",
        value_fn=lambda device, info: device.get("sessionDistance"),
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
    ),
    SolarEdgeSensorDescription(
        key="charger_status",
        translation_key="charger_status",
        value_fn=lambda device, info: device.get("chargerStatus"),
    ),
    SolarEdgeSensorDescription(
        key="connection_status",
        translation_key="connection_status",
        value_fn=lambda device, info: device.get("connectionStatus"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="activation_mode",
        translation_key="activation_mode",
        value_fn=lambda device, info: device.get("activationMode"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="activation_state",
        translation_key="activation_state",
        value_fn=lambda device, info: device.get("activationState"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="schedule_title",
        translation_key="schedule_title",
        value_fn=lambda device, info: device.get("scheduleTitle"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="available_action",
        translation_key="available_action",
        value_fn=lambda device, info: _available_action(device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="session_solar_usage",
        translation_key="session_solar_usage",
        value_fn=lambda device, info: device.get("sessionSolarUsage"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="excess_pv",
        translation_key="excess_pv",
        value_fn=lambda device, info: device.get("excessPV"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="next_schedule_start",
        translation_key="next_schedule_start",
        value_fn=lambda device, info: _ms_timestamp(
            (device.get("scheduleInfo") or {}).get("startDate")
        ),
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="next_schedule_end",
        translation_key="next_schedule_end",
        value_fn=lambda device, info: _ms_timestamp(
            (device.get("scheduleInfo") or {}).get("endDate")
        ),
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="rated_power",
        translation_key="rated_power",
        value_fn=lambda device, info: device.get("ratedPower"),
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarEdgeSensorDescription(
        key="vehicle",
        translation_key="vehicle",
        value_fn=lambda device, info: (info.get("vehicleInfo") or {}).get("alias")
        or (device.get("latestSessionApplianceAlias") or {}).get("VEHICLE")
        or ((device.get("applianceData") or {}).get("alias")),
        attributes_fn=lambda device, info: _vehicle_attributes(device, info),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEdge Home Automation sensors from a config entry."""
    coordinator: SolarEdgeHomeAutomationCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    site_id = entry.data[CONF_SITE_ID]

    entities = []
    for device in coordinator.data.smart_devices:
        entities.extend(
            SolarEdgeHomeAutomationSensor(coordinator, site_id, device, description)
            for description in SMART_DEVICE_SENSORS
        )
    for device in coordinator.data.ev_chargers:
        entities.extend(
            SolarEdgeHomeAutomationSensor(coordinator, site_id, device, description)
            for description in EV_CHARGER_SENSORS
        )
    async_add_entities(entities)


class SolarEdgeHomeAutomationSensor(
    SolarEdgeHomeAutomationEntity,
    SensorEntity,
):
    """SolarEdge Home Automation sensor."""

    entity_description: SolarEdgeSensorDescription

    def __init__(
        self,
        coordinator: SolarEdgeHomeAutomationCoordinator,
        site_id: str,
        device: dict[str, Any],
        description: SolarEdgeSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            site_id=site_id,
            device=device,
            key=description.key,
        )
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        device = self.current_device
        if device is None:
            return None
        info = self.coordinator.data.ev_charger_info.get(self.device_id, {})
        return self.entity_description.value_fn(device, info)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional sensor attributes."""
        device = self.current_device
        if device is None:
            return {}
        info = self.coordinator.data.ev_charger_info.get(self.device_id, {})
        attributes = {
            "communication_status": device.get("communicationStatus"),
            "device_status": device.get("deviceStatus"),
            "serial_number": device.get("serialNumber"),
        }
        if self.entity_description.attributes_fn is not None:
            attributes.update(self.entity_description.attributes_fn(device, info))
        return {key: value for key, value in attributes.items() if value is not None}


def _wh_to_kwh(value: Any) -> float | None:
    """Convert Wh to kWh."""
    if value is None:
        return None
    return round(float(value) / 1000, 3)


def _ms_timestamp(value: Any) -> datetime | None:
    """Convert a millisecond Unix timestamp to datetime."""
    if value is None:
        return None
    return datetime.fromtimestamp(float(value) / 1000).astimezone()


def _vehicle_attributes(device: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    """Return vehicle metadata attributes."""
    vehicle = info.get("vehicleInfo") or device.get("applianceData") or {}
    return {
        "manufacturer": vehicle.get("manufacturer"),
        "model": vehicle.get("model"),
        "manufacturer_year": vehicle.get("manufacturerYear"),
        "origin": vehicle.get("origin"),
    }


def _available_action(device: dict[str, Any]) -> str | None:
    """Return the first available SolarEdge action label."""
    actions = device.get("actionOperationDetails") or []
    if not actions:
        return None
    action = actions[0]
    return action.get("actionText") or action.get("actionOp")
