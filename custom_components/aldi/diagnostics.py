"""Diagnostics support for ALDI weekly offers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "api_key",
    "password",
    "token",
    "session",
    "webhook_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    data = coordinator.data or {}

    diagnostics_data = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
        },
        "coordinator": {
            "region": coordinator.region,
            "consecutive_failures": coordinator._consecutive_failures,
            "last_success": coordinator._last_success.isoformat()
            if coordinator._last_success
            else None,
            "backoff_until": coordinator._backoff_until.isoformat()
            if coordinator._backoff_until
            else None,
            "has_data": coordinator.data is not None,
            "sued_current_url": coordinator.sued_current_url,
            "nord_current_url": coordinator.nord_current_url,
            "sued_offers_count": len(data.get("sued_discounts", [])),
            "sued_next_offers_count": len(data.get("sued_next_discounts", [])),
            "sued_preview_offers_count": len(data.get("sued_preview_discounts", [])),
            "nord_offers_count": len(data.get("nord_discounts", [])),
            "nord_next_offers_count": len(data.get("nord_next_discounts", [])),
            "nord_preview_offers_count": len(data.get("nord_preview_discounts", [])),
        },
    }

    return diagnostics_data
