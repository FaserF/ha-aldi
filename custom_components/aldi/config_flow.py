"""Config flow for ALDI weekly offers integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import (
    CONF_COUNTRY,
    CONF_REGION,
    CONF_UPDATE_INTERVAL,
    COUNTRY_AT,
    COUNTRY_CH,
    COUNTRY_DE,
    COUNTRY_HU,
    COUNTRY_IT,
    COUNTRY_SI,
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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_data: dict[str, Any] = {}
        self._country: str | None = None

    async def async_step_integration_discovery(
        self, discovery_info: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle a discovered ALDI region (triggered by location-based auto-discovery)."""
        region = discovery_info.get(CONF_REGION, "")
        if not region:
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(f"aldi_{region}")
        self._abort_if_unique_id_configured()

        self._discovery_data = discovery_info
        self.context["title_placeholders"] = {
            "region_label": discovery_info.get("region_label", "ALDI"),
        }
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm adding the discovered ALDI region."""
        if user_input is not None:
            region = self._discovery_data.get(CONF_REGION, REGION_BOTH)
            region_label = self._discovery_data.get("region_label", "ALDI")
            title_map = {
                REGION_SUED: "ALDI SÜD Offers",
                REGION_NORD: "ALDI NORD Offers",
                REGION_BOTH: "ALDI SÜD & NORD Offers",
            }
            title = title_map.get(region, f"{region_label} Offers")
            return self.async_create_entry(
                title=title,
                data={CONF_COUNTRY: COUNTRY_DE, CONF_REGION: region},
            )

        return self.async_show_form(step_id="discovery_confirm")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial user input step (Country selection)."""
        _LOGGER.debug("async_step_user called with input: %s", user_input)
        errors: dict[str, str] = {}

        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            if self._country == COUNTRY_DE:
                return await self.async_step_region()

            # For other countries, configure directly using SÜD-style parsing structure
            await self.async_set_unique_id(f"aldi_{self._country}")
            self._abort_if_unique_id_configured()

            title_map = {
                COUNTRY_AT: "HOFER Österreich Offers",
                COUNTRY_CH: "ALDI Suisse Offers",
                COUNTRY_HU: "ALDI Magyarország Offers",
                COUNTRY_IT: "ALDI Italia Offers",
                COUNTRY_SI: "HOFER Slovenija Offers",
            }
            title = title_map.get(self._country, "ALDI Offers")

            return self.async_create_entry(
                title=title,
                data={
                    CONF_COUNTRY: self._country,
                    CONF_REGION: self._country,  # Map region to country code to isolate caches
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_COUNTRY, default=COUNTRY_DE): selector(
                    {
                        "select": {
                            "options": [
                                {"value": COUNTRY_DE, "label": "Germany (Deutschland)"},
                                {
                                    "value": COUNTRY_AT,
                                    "label": "Austria (Österreich / HOFER)",
                                },
                                {
                                    "value": COUNTRY_CH,
                                    "label": "Switzerland (Suisse / ALDI)",
                                },
                                {
                                    "value": COUNTRY_HU,
                                    "label": "Hungary (Magyarország / ALDI)",
                                },
                                {"value": COUNTRY_IT, "label": "Italy (Italia / ALDI)"},
                                {
                                    "value": COUNTRY_SI,
                                    "label": "Slovenia (Slovenija / HOFER)",
                                },
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

    async def async_step_region(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle region selection step if Germany is selected."""
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
                data={
                    CONF_COUNTRY: COUNTRY_DE,
                    CONF_REGION: region,
                },
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
            step_id="region",
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
