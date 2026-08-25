"""Buttons for SolarEdge Home Automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SITE_ID, DATA_COORDINATOR, DOMAIN
from .coordinator import SolarEdgeHomeAutomationCoordinator
from .entity import SolarEdgeHomeAutomationEntity


@dataclass(frozen=True, kw_only=True)
class SolarEdgeButtonDescription(ButtonEntityDescription):
    """Description for a SolarEdge Home Automation button."""

    press_fn: str


EV_CHARGER_BUTTONS: tuple[SolarEdgeButtonDescription, ...] = (
    SolarEdgeButtonDescription(
        key="charge_now",
        translation_key="charge_now",
        press_fn="async_charge_now",
    ),
    SolarEdgeButtonDescription(
        key="stop_charging",
        translation_key="stop_charging",
        press_fn="async_stop_charging",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEdge Home Automation buttons from a config entry."""
    coordinator: SolarEdgeHomeAutomationCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    site_id = entry.data[CONF_SITE_ID]
    async_add_entities(
        SolarEdgeHomeAutomationButton(coordinator, site_id, device, description)
        for device in coordinator.data.ev_chargers
        for description in EV_CHARGER_BUTTONS
    )


class SolarEdgeHomeAutomationButton(SolarEdgeHomeAutomationEntity, ButtonEntity):
    """SolarEdge Home Automation button."""

    entity_description: SolarEdgeButtonDescription

    def __init__(
        self,
        coordinator: SolarEdgeHomeAutomationCoordinator,
        site_id: str,
        device: dict[str, Any],
        description: SolarEdgeButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator,
            site_id=site_id,
            device=device,
            key=description.key,
        )
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle button press."""
        method = getattr(self.coordinator, self.entity_description.press_fn)
        await method(self.device_id)
