"""ALDI Weekly Offers button platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, REGION_BOTH, REGION_NORD, REGION_SUED
from .coordinator import AldiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: Any,
) -> None:
    """Set up ALDI force-update buttons from a config entry."""
    coordinator: AldiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    region = coordinator.region

    entities: list[ButtonEntity] = []

    if region in (REGION_SUED, REGION_BOTH):
        entities.append(AldiForceUpdateButton(coordinator, REGION_SUED))
    if region in (REGION_NORD, REGION_BOTH):
        entities.append(AldiForceUpdateButton(coordinator, REGION_NORD))

    async_add_entities(entities, update_before_add=False)


class AldiForceUpdateButton(ButtonEntity):
    """Button to manually trigger an ALDI weekly offers refresh."""

    _attr_icon = "mdi:refresh"
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AldiDataUpdateCoordinator, side: str) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._side = side

        if side == REGION_SUED:
            label = "ALDI SÜD"
            device_id = f"aldi_sued_{coordinator.region}"
            config_url = coordinator.sued_current_url
        else:
            label = "ALDI NORD"
            device_id = f"aldi_nord_{coordinator.region}"
            config_url = coordinator.nord_current_url

        self._attr_name = f"{label} Force Update"
        self._attr_unique_id = f"aldi_{side}_{coordinator.region}_force_update"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"{label} Offers",
            manufacturer=label,
            model="Weekly Flyer",
            configuration_url=config_url,
        )

    async def async_press(self) -> None:
        """Trigger a coordinator refresh."""
        _LOGGER.info(
            "Manual ALDI %s weekly offers refresh triggered", self._side.upper()
        )
        await self.coordinator.async_request_refresh()
