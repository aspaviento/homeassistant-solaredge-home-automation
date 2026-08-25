"""The SolarEdge Home Automation integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_SITE_ID, DATA_COORDINATOR, DOMAIN
from .coordinator import SolarEdgeHomeAutomationCoordinator

PLATFORMS: tuple[Platform, ...] = (
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdge Home Automation from a config entry."""
    coordinator = SolarEdgeHomeAutomationCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    site_id = entry.data[CONF_SITE_ID]
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, site_id)},
        manufacturer="SolarEdge",
        name=f"SolarEdge Site {site_id}",
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload SolarEdge Home Automation."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
