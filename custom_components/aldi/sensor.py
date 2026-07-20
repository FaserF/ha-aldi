"""ALDI weekly offers sensor platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    ATTR_DISCOUNTS,
    ATTR_VALID_DATE,
    DOMAIN,
    REGION_BOTH,
    REGION_NORD,
    REGION_SUED,
    COUNTRY_DE,
    COUNTRY_AT,
    COUNTRY_CH,
    COUNTRY_HU,
    COUNTRY_IT,
    COUNTRY_SI,
)
from .coordinator import AldiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by ALDI SÜD & NORD digital brochures"


def is_recipe(discount: dict[str, Any]) -> bool:
    """Check if a discount/offer item is actually a recipe."""
    title = str(discount.get("product", "")).lower()
    base_price = str(discount.get("base_price", "")).lower()
    return (
        "zutaten für" in base_price
        or "zubereitung" in base_price
        or "zutaten für" in title
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: Any,
) -> None:
    """Set up ALDI weekly offers sensors from a config entry."""
    coordinator: AldiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    country = coordinator.country
    region = coordinator.region

    entities: list[SensorEntity] = []

    if country != COUNTRY_DE or region in (REGION_SUED, REGION_BOTH):
        entities.append(AldiSuedSensor(coordinator))
        entities.append(AldiSuedNextSensor(coordinator))
        entities.append(AldiSuedPreviewSensor(coordinator))
        entities.append(AldiSuedRecipesSensor(coordinator))
        entities.append(AldiSuedRecipesNextSensor(coordinator))
        entities.append(AldiSuedRecipesPreviewSensor(coordinator))

    if country == COUNTRY_DE and region in (REGION_NORD, REGION_BOTH):
        entities.append(AldiNordSensor(coordinator))
        entities.append(AldiNordNextSensor(coordinator))
        entities.append(AldiNordPreviewSensor(coordinator))
        entities.append(AldiNordRecipesSensor(coordinator))
        entities.append(AldiNordRecipesNextSensor(coordinator))
        entities.append(AldiNordRecipesPreviewSensor(coordinator))

    async_add_entities(entities, update_before_add=False)


def get_country_metadata(country: str) -> dict[str, str]:
    """Get dynamic display name and manufacturer based on country code."""
    if country == COUNTRY_AT:
        return {"name": "HOFER", "manufacturer": "HOFER"}
    if country == COUNTRY_CH:
        return {"name": "ALDI Suisse", "manufacturer": "ALDI Suisse"}
    if country == COUNTRY_HU:
        return {"name": "ALDI Hungary", "manufacturer": "ALDI"}
    if country == COUNTRY_IT:
        return {"name": "ALDI Italy", "manufacturer": "ALDI"}
    if country == COUNTRY_SI:
        return {"name": "HOFER Slovenia", "manufacturer": "HOFER"}
    return {"name": "ALDI SÜD", "manufacturer": "ALDI SÜD"}


class AldiSuedSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents current ALDI SÜD weekly offers (Aktuelle Woche)."""

    _attr_icon = "mdi:cart-percent"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = None
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of current offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiSuedNextSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents upcoming ALDI SÜD weekly offers (Nächste Woche)."""

    _attr_icon = "mdi:calendar-arrow-right"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = "Next"
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_next_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_next_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_next_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiSuedPreviewSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents upcoming ALDI SÜD weekly offers (Vorschau)."""

    _attr_icon = "mdi:calendar-arrow-right"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = "Preview"
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_preview"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_preview_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_preview_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_preview_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiSuedRecipesSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents current ALDI SÜD recipes (Aktuelle Woche)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = "Recipes"
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_recipes_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of current recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiSuedRecipesNextSensor(
    CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity
):
    """Represents upcoming ALDI SÜD recipes (Nächste Woche)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = "Recipes Next"
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_recipes_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of upcoming recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_next_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return upcoming recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_next_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_next_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiSuedRecipesPreviewSensor(
    CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity
):
    """Represents upcoming ALDI SÜD recipes (Vorschau)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = get_country_metadata(coordinator.country)
        self._attr_name = "Recipes Preview"
        self._attr_unique_id = f"aldi_sued_{coordinator.region}_recipes_preview"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_sued_{coordinator.region}")},
            name=f"{meta['name']} Offers",
            manufacturer=meta["manufacturer"],
            model="Weekly Flyer",
            configuration_url=coordinator.sued_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("sued_preview_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("sued_preview_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("sued_preview_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents current ALDI NORD weekly offers (Aktuelle Woche)."""

    _attr_icon = "mdi:cart-percent"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = None
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of current offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordNextSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents upcoming ALDI NORD weekly offers (Nächste Woche)."""

    _attr_icon = "mdi:calendar-arrow-right"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = "Next"
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_next_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_next_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_next_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordPreviewSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents upcoming ALDI NORD weekly offers (Vorschau)."""

    _attr_icon = "mdi:calendar-arrow-right"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = "Preview"
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_preview"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview offers."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_preview_discounts", [])
        return len([d for d in discounts if not is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview offer attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_preview_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if not is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_preview_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordRecipesSensor(CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity):
    """Represents current ALDI NORD recipes (Aktuelle Woche)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = "Recipes"
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_recipes_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of current recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordRecipesNextSensor(
    CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity
):
    """Represents upcoming ALDI NORD recipes (Nächste Woche)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = "Recipes Next"
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_recipes_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of upcoming recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_next_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return upcoming recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_next_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_next_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class AldiNordRecipesPreviewSensor(
    CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity
):
    """Represents upcoming ALDI NORD recipes (Vorschau)."""

    _attr_icon = "mdi:chef-hat"
    _attr_native_unit_of_measurement = "items"
    _attr_has_entity_name = True
    _attr_name = "Recipes Preview"
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = frozenset({ATTR_DISCOUNTS})

    def __init__(self, coordinator: AldiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"aldi_nord_{coordinator.region}_recipes_preview"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"aldi_nord_{coordinator.region}")},
            name="ALDI NORD Offers",
            manufacturer="ALDI NORD",
            model="Weekly Flyer",
            configuration_url=coordinator.nord_current_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of preview recipes."""
        if not self.coordinator.data:
            return None
        discounts = self.coordinator.data.get("nord_preview_discounts", [])
        return len([d for d in discounts if is_recipe(d)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return preview recipe attributes."""
        data = self.coordinator.data or {}
        discounts = data.get("nord_preview_discounts", [])
        return {
            ATTR_DISCOUNTS: [d for d in discounts if is_recipe(d)],
            ATTR_VALID_DATE: data.get("nord_preview_valid_until"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
