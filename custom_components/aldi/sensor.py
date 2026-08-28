"""ALDI weekly offers sensor platform."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant import config_entries
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DISCOUNTS,
    ATTR_VALID_DATE,
    COUNTRY_AT,
    COUNTRY_CH,
    COUNTRY_DE,
    COUNTRY_HU,
    COUNTRY_IT,
    COUNTRY_SI,
    DOMAIN,
    REGION_BOTH,
    REGION_NORD,
    REGION_SUED,
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

    product_filters = getattr(coordinator, "product_filters", []) or []
    for product_filter in product_filters:
        if product_filter and str(product_filter).strip():
            entities.append(
                AldiProductFilterSensor(coordinator, str(product_filter).strip())
            )

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


class AldiProductFilterSensor(
    CoordinatorEntity[AldiDataUpdateCoordinator], SensorEntity
):
    """Represents a product filter sensor tracking specific offers."""

    _attr_icon = "mdi:tag-search"
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({"matches"})

    def __init__(
        self, coordinator: AldiDataUpdateCoordinator, product_filter: str
    ) -> None:
        """Initialize the product filter sensor."""
        super().__init__(coordinator)
        self.product_filter = product_filter
        slug_filter = re.sub(r"[^a-zA-Z0-9_-]", "_", product_filter.lower())
        self._attr_unique_id = f"aldi_{coordinator.region}_filter_{slug_filter}"
        self._attr_name = f"Filter {product_filter}"

        if coordinator.region == REGION_NORD:
            dev_id = f"aldi_nord_{coordinator.region}"
            dev_name = "ALDI NORD Offers"
            dev_mfr = "ALDI NORD"
            config_url = coordinator.nord_current_url
        else:
            meta = get_country_metadata(coordinator.country)
            dev_id = f"aldi_sued_{coordinator.region}"
            dev_name = f"{meta['name']} Offers"
            dev_mfr = meta["manufacturer"]
            config_url = coordinator.sued_current_url

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dev_id)},
            name=dev_name,
            manufacturer=dev_mfr,
            model="Weekly Flyer",
            configuration_url=config_url,
        )

    def _get_discounts(self) -> list[dict[str, Any]]:
        """Get all discount items from coordinator data."""
        if not self.coordinator.data:
            return []
        if "discounts" in self.coordinator.data:
            return self.coordinator.data.get("discounts") or []
        sued = self.coordinator.data.get("sued_discounts") or []
        nord = self.coordinator.data.get("nord_discounts") or []
        return sued + nord

    def _get_matches(self) -> list[dict[str, Any]]:
        """Find matching offers for the configured product filter."""
        discounts = self._get_discounts()
        term = self.product_filter.lower()
        matches: list[dict[str, Any]] = []
        for item in discounts:
            prod_name = str(item.get("product", "")).lower()
            cat_name = str(item.get("category", "")).lower()
            base_price = str(item.get("base_price", "")).lower()
            if term in prod_name or term in cat_name or term in base_price:
                matches.append(item)
        return matches

    @staticmethod
    def _parse_price(price_val: Any) -> float | None:
        """Parse price string to float for comparison."""
        if price_val is None:
            return None
        if isinstance(price_val, (int, float)):
            return float(price_val)
        price_str = str(price_val).strip()
        if not price_str:
            return None
        match = re.search(r"(\d+(?:[.,]\d+)?)", price_str.replace(" ", ""))
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
        return None

    def _get_best_match(self, matches: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Find the offer with the lowest (best) price."""
        if not matches:
            return None
        best_item: dict[str, Any] | None = None
        min_price = float("inf")
        for item in matches:
            price = self._parse_price(item.get("price"))
            if price is not None and price < min_price:
                min_price = price
                best_item = item
        return best_item or matches[0]

    def _get_valid_until(self) -> str | None:
        """Get valid_until date string."""
        if not self.coordinator.data:
            return None
        return (
            self.coordinator.data.get("valid_until")
            or self.coordinator.data.get("sued_valid_until")
            or self.coordinator.data.get("nord_valid_until")
        )

    @property
    def native_value(self) -> str:
        """Return the best price found or 'Nicht im Angebot'."""
        if not self.coordinator.data:
            return "Nicht im Angebot"
        matches = self._get_matches()
        if not matches:
            return "Nicht im Angebot"
        best = self._get_best_match(matches)
        if best and best.get("price"):
            return str(best["price"])
        return "Im Angebot"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return product filter attributes."""
        matches = self._get_matches() if self.coordinator.data else []
        on_sale = len(matches) > 0
        best_match = self._get_best_match(matches) if on_sale else None
        valid_until = (
            best_match.get("valid_until")
            if best_match and best_match.get("valid_until")
            else self._get_valid_until()
        )

        return {
            "filter": self.product_filter,
            "on_sale": on_sale,
            "match_count": len(matches),
            "best_price": best_match.get("price") if best_match else None,
            "base_price": best_match.get("base_price") if best_match else None,
            "product_title": best_match.get("product") if best_match else None,
            "category": best_match.get("category") if best_match else None,
            "valid_until": valid_until,
            "picture_link": best_match.get("picture_link") if best_match else None,
            "matches": matches,
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
