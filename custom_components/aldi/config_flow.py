"""Config flow for ALDI weekly offers integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import (
    CONF_REGION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    REGION_BOTH,
    REGION_NORD,
    REGION_SUED,
)

_LOGGER = logging.getLogger(__name__)


class AldiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ALDI weekly offers."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial user input step."""
        _LOGGER.debug("async_step_user called with input: %s", user_input)
        errors: dict[str, str] = {}

        if user_input is not None:
            region = user_input[CONF_REGION]
            await self.async_set_unique_id(f"aldi_{region}")
            self._abort_if_unique_id_configured()

            title_map = {
                REGION_SUED: "ALDI SÜD Offers",
                REGION_NORD: "ALDI NORD Offers",
                REGION_BOTH: "ALDI SÜD & NORD Offers",
            }
            title = title_map.get(region, "ALDI Offers")

            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=REGION_BOTH): selector(
                    {
                        "select": {
                            "options": [
                                {"value": REGION_SUED, "label": "ALDI SÜD"},
                                {"value": REGION_NORD, "label": "ALDI NORD"},
                                {"value": REGION_BOTH, "label": "ALDI SÜD & NORD"},
                            ]
                        }
                    }
                )
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AldiOptionsFlowHandler:
        """Return the options flow handler."""
        return AldiOptionsFlowHandler(config_entry)


class AldiOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ALDI weekly offers."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
