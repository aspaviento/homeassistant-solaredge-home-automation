"""The SolarEdge Home Automation integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er

from .const import CONF_SITE_ID, DATA_COORDINATOR, DOMAIN
from .coordinator import SolarEdgeHomeAutomationCoordinator

SERVICE_TURN_ON_FOR = "turn_on_for"

SERVICE_TURN_ON_FOR_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required("duration"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }
)

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
    _async_register_services(hass)
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
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_TURN_ON_FOR)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    if hass.services.has_service(DOMAIN, SERVICE_TURN_ON_FOR):
        return

    async def async_turn_on_for(call: ServiceCall) -> None:
        """Handle a timed Smart Energy device turn-on service call."""
        duration = call.data["duration"]
        entity_ids = call.data[ATTR_ENTITY_ID]
        targets = _async_smart_device_targets(hass, entity_ids)

        for coordinator, device_id in targets:
            await coordinator.async_turn_on_device_for(device_id, duration)

    hass.services.async_register(
        DOMAIN,
        SERVICE_TURN_ON_FOR,
        async_turn_on_for,
        schema=SERVICE_TURN_ON_FOR_SCHEMA,
    )


def _async_smart_device_targets(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> set[tuple[SolarEdgeHomeAutomationCoordinator, str]]:
    """Return Smart Device targets for a service call."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    targets: set[tuple[SolarEdgeHomeAutomationCoordinator, str]] = set()

    for entity_id in entity_ids:
        registry_entry = entity_registry.async_get(entity_id)
        if registry_entry is None or registry_entry.platform != DOMAIN:
            raise HomeAssistantError(
                f"{entity_id} is not a SolarEdge Home Automation entity"
            )

        if registry_entry.device_id is None:
            raise HomeAssistantError(
                f"{entity_id} does not map to a SolarEdge Home Automation device"
            )

        device_entry = device_registry.async_get(registry_entry.device_id)
        if device_entry is None:
            raise HomeAssistantError(
                f"{entity_id} does not map to a SolarEdge Home Automation device"
            )

        identifiers = [
            identifier
            for identifier in device_entry.identifiers
            if len(identifier) == 3 and identifier[0] == DOMAIN
        ]
        if not identifiers:
            raise HomeAssistantError(
                f"{entity_id} does not map to a SolarEdge Home Automation device"
            )

        _, site_id, device_id = identifiers[0]
        coordinator = _coordinator_for_site(hass, site_id)
        if coordinator is None:
            raise HomeAssistantError(f"No SolarEdge Home Automation site for {entity_id}")

        if not any(
            str(device.get("reporterId") or device.get("deviceId")) == device_id
            for device in coordinator.data.smart_devices
        ):
            raise HomeAssistantError(f"{entity_id} is not a Smart Energy device")

        targets.add((coordinator, device_id))

    return targets


def _coordinator_for_site(
    hass: HomeAssistant,
    site_id: str,
) -> SolarEdgeHomeAutomationCoordinator | None:
    """Return the coordinator for a SolarEdge site."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        coordinator = entry_data[DATA_COORDINATOR]
        if coordinator.config_entry.data[CONF_SITE_ID] == site_id:
            return coordinator
    return None
