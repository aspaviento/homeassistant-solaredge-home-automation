"""Number entities for SolarEdge Home Automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_SITE_ID,
    DATA_COORDINATOR,
    DEFAULT_TIMER_DURATION_MINUTES,
    DOMAIN,
    MAX_TIMER_DURATION_MINUTES,
    MIN_TIMER_DURATION_MINUTES,
)
from .coordinator import SolarEdgeHomeAutomationCoordinator
from .entity import SolarEdgeHomeAutomationEntity


@dataclass(frozen=True, kw_only=True)
class SolarEdgeNumberDescription(NumberEntityDescription):
    """Description for a SolarEdge Home Automation number entity."""


SMART_DEVICE_NUMBERS: tuple[SolarEdgeNumberDescription, ...] = (
    SolarEdgeNumberDescription(
        key="timer_duration",
        translation_key="timer_duration",
        native_min_value=MIN_TIMER_DURATION_MINUTES,
        native_max_value=MAX_TIMER_DURATION_MINUTES,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEdge Home Automation numbers from a config entry."""
    coordinator: SolarEdgeHomeAutomationCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    site_id = entry.data[CONF_SITE_ID]
    async_add_entities(
        SolarEdgeHomeAutomationNumber(coordinator, site_id, device, description)
        for device in coordinator.data.smart_devices
        for description in SMART_DEVICE_NUMBERS
    )


class SolarEdgeHomeAutomationNumber(
    SolarEdgeHomeAutomationEntity,
    NumberEntity,
    RestoreEntity,
):
    """SolarEdge Home Automation number entity."""

    entity_description: SolarEdgeNumberDescription

    def __init__(
        self,
        coordinator: SolarEdgeHomeAutomationCoordinator,
        site_id: str,
        device: dict[str, Any],
        description: SolarEdgeNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(
            coordinator,
            site_id=site_id,
            device=device,
            key=description.key,
        )
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        """Restore the last selected timer duration."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            self.coordinator.set_timer_duration(
                self.device_id,
                DEFAULT_TIMER_DURATION_MINUTES,
            )
            return

        try:
            duration = int(float(last_state.state))
        except ValueError:
            duration = DEFAULT_TIMER_DURATION_MINUTES
        self.coordinator.set_timer_duration(self.device_id, duration)

    @property
    def native_value(self) -> int:
        """Return the selected timer duration."""
        return self.coordinator.timer_duration_minutes.get(
            self.device_id,
            DEFAULT_TIMER_DURATION_MINUTES,
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the selected timer duration."""
        self.coordinator.set_timer_duration(self.device_id, int(value))
        self.async_write_ha_state()
