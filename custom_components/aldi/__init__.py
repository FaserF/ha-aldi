"""ALDI weekly offers – Home Assistant Custom Component."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries, core
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_REGION,
    DISCOVERY_NORD_LAT_BOUNDARY,
    DOMAIN,
    PLATFORMS,
    REGION_BOTH,
    REGION_NORD,
    REGION_SUED,
)
from .coordinator import AldiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Countries where ALDI operates with NORD/SÜD split (DE) or only SÜD (AT, CH, …)
_ALDI_SUED_ONLY_COUNTRIES = {"AT", "CH", "AU", "GB", "IE", "US"}
_ALDI_RELEVANT_COUNTRIES = {
    "DE",
    "AT",
    "CH",
    "AU",
    "GB",
    "IE",
    "US",
    "NL",
    "BE",
    "PL",
    "PT",
    "ES",
    "FR",
}


async def async_setup(hass: core.HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the ALDI integration.

    When 'aldi:' is listed in configuration.yaml (zero-entry bootstrap),
    this is the only hook HA calls.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get("_discovery_scheduled"):
        domain_data["_discovery_scheduled"] = True

        async def _on_ha_started(event: core.Event) -> None:  # noqa: RUF100
            await _async_discover_region(hass)

        if hass.is_running:
            hass.async_create_task(_async_discover_region(hass))
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)

    return True


async def _async_discover_region(hass: core.HomeAssistant) -> None:
    """Determine the correct ALDI region from HA location and trigger discovery."""
    ha_lat = hass.config.latitude
    ha_lon = hass.config.longitude

    if not ha_lat or not ha_lon:
        _LOGGER.debug("ALDI discovery: HA home location not set, skipping")
        return

    ha_country: str = (getattr(hass.config, "country", None) or "").upper()
    if ha_country and ha_country not in _ALDI_RELEVANT_COUNTRIES:
        _LOGGER.debug(
            "ALDI discovery: country %s not an ALDI market, skipping", ha_country
        )
        return

    # Determine region:
    # - Outside Germany → always ALDI SÜD (international stores are Süd-affiliated)
    # - Germany, latitude >= boundary → ALDI NORD territory
    # - Germany, latitude < boundary  → ALDI SÜD territory
    if ha_country == "DE":
        if ha_lat >= DISCOVERY_NORD_LAT_BOUNDARY:
            suggested_region = REGION_NORD
            region_label = "ALDI NORD"
        else:
            suggested_region = REGION_SUED
            region_label = "ALDI SÜD"
    else:
        suggested_region = REGION_SUED
        region_label = "ALDI SÜD"

    _LOGGER.debug(
        "ALDI discovery: detected region '%s'",
        suggested_region,
    )

    # Check if this specific region (or BOTH) is already configured
    configured_regions = {
        entry.data.get(CONF_REGION)
        for entry in hass.config_entries.async_entries(DOMAIN)
    }
    if suggested_region in configured_regions or REGION_BOTH in configured_regions:
        _LOGGER.debug(
            "ALDI discovery: region '%s' is already configured, skipping",
            suggested_region,
        )
        return

    _LOGGER.debug(
        "ALDI discovery: triggering flow for region '%s' (%s)",
        suggested_region,
        region_label,
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_REGION: suggested_region,
                "region_label": region_label,
            },
        )
    )


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up ALDI weekly offers from a config entry."""
    _LOGGER.debug(
        "Setting up ALDI entry: %s (region: %s)",
        entry.entry_id,
        entry.data.get(CONF_REGION),
    )
    hass.data.setdefault(DOMAIN, {})

    coordinator = AldiDataUpdateCoordinator(hass, entry)
    await coordinator.async_load_cache()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        if not coordinator.data:
            raise ConfigEntryNotReady(
                f"Cannot fetch ALDI offers for region {coordinator.region}: {err}"
            ) from err
        _LOGGER.warning(
            "Initial ALDI update failed for region %s, using cached data. Error: %s",
            coordinator.region,
            err,
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    domain_data = hass.data[DOMAIN]
    if not domain_data.get("_discovery_scheduled"):
        domain_data["_discovery_scheduled"] = True

        async def _on_ha_started(event: core.Event) -> None:  # noqa: RUF100
            await _async_discover_region(hass)

        if hass.is_running:
            hass.async_create_task(_async_discover_region(hass))
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)

    _LOGGER.debug("Finished setting up ALDI entry: %s", entry.entry_id)
    return True


async def _async_update_options(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> None:
    """Reload the entry when options change."""
    _LOGGER.debug(
        "Reloading ALDI entry %s due to option updates. New options: %s",
        entry.entry_id,
        entry.options,
    )
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading ALDI entry: %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    _LOGGER.debug("Unload result for ALDI entry %s: %s", entry.entry_id, unload_ok)
    return unload_ok
