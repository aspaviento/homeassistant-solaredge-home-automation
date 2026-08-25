"""Config flow for SolarEdge Home Automation."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import (
    SolarEdgeHomeAutomationApiError,
    SolarEdgeHomeAutomationAuthError,
    SolarEdgeHomeAutomationClient,
)
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SITE_ID,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)


class SolarEdgeHomeAutomationConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a SolarEdge Home Automation config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate_input(user_input)
            if not errors:
                site_id = str(user_input[CONF_SITE_ID]).strip()
                await self.async_set_unique_id(site_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SolarEdge Home Automation {site_id}",
                    data={
                        CONF_SITE_ID: site_id,
                        CONF_USERNAME: str(user_input[CONF_USERNAME]).strip(),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SCAN_INTERVAL: _scan_interval(user_input),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SolarEdgeHomeAutomationOptionsFlow(config_entry)

    async def _async_validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate setup data."""
        errors = _validate_static_input(user_input)
        if errors:
            return errors

        client = SolarEdgeHomeAutomationClient(
            username=str(user_input[CONF_USERNAME]).strip(),
            password=user_input[CONF_PASSWORD],
            site_id=str(user_input[CONF_SITE_ID]).strip(),
            session=async_get_clientsession(self.hass),
        )
        try:
            await client.async_get_site_devices()
        except SolarEdgeHomeAutomationAuthError:
            errors["base"] = "invalid_auth"
        except (SolarEdgeHomeAutomationApiError, ClientResponseError, ClientError, TimeoutError):
            errors["base"] = "cannot_connect"
        return errors


class SolarEdgeHomeAutomationOptionsFlow(config_entries.OptionsFlow):
    """Handle SolarEdge Home Automation options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_options_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title="",
                    data={CONF_SCAN_INTERVAL: _scan_interval(user_input)},
                )

        defaults = {
            CONF_SCAN_INTERVAL: self._entry.options.get(
                CONF_SCAN_INTERVAL,
                self._entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(user_input or defaults),
            errors=errors,
        )


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return setup schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_SITE_ID, default=defaults.get(CONF_SITE_ID, "")): str,
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL_MINUTES,
                    max=MAX_SCAN_INTERVAL_MINUTES,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
        }
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return options schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults[CONF_SCAN_INTERVAL],
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL_MINUTES,
                    max=MAX_SCAN_INTERVAL_MINUTES,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
        }
    )


def _validate_static_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate local setup fields."""
    errors = _validate_options_input(user_input)
    for key in (CONF_SITE_ID, CONF_USERNAME, CONF_PASSWORD):
        if not str(user_input.get(key, "")).strip():
            errors[key] = "required"
    return errors


def _validate_options_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate options fields."""
    errors: dict[str, str] = {}
    try:
        interval = _scan_interval(user_input)
    except (TypeError, ValueError):
        errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
        return errors
    if not MIN_SCAN_INTERVAL_MINUTES <= interval <= MAX_SCAN_INTERVAL_MINUTES:
        errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
    return errors


def _scan_interval(user_input: dict[str, Any]) -> int:
    """Return scan interval as a whole number of minutes."""
    value = float(user_input[CONF_SCAN_INTERVAL])
    if not value.is_integer():
        raise ValueError("scan interval must be a whole number")
    return int(value)
