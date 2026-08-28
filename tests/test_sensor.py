"""Test the ALDI weekly offers sensors."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import CONF_REGION, DOMAIN, REGION_BOTH
from custom_components.aldi.sensor import AldiProductFilterSensor, async_setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_sensors_setup(hass: HomeAssistant) -> None:
    """Test setting up sensors and verifying state attributes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_BOTH},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.country = "de"
    coordinator.region = REGION_BOTH
    coordinator.product_filters = []
    coordinator.sued_current_url = "https://sued-url"
    coordinator.nord_current_url = "https://nord-url"

    mock_data = {
        "sued_discounts": [
            {"product": "Sued Product", "price": "1.00", "base_price": "unit"},
            {
                "product": "Warme Melonensuppe",
                "price": "",
                "base_price": "Zutaten für 4 Portionen",
            },
        ],
        "sued_next_discounts": [],
        "sued_preview_discounts": [],
        "sued_valid_until": "13.7",
        "nord_discounts": [
            {"product": "Nord Product", "price": "2.00", "base_price": "unit2"}
        ],
        "nord_next_discounts": [
            {"product": "Nord Next Product", "price": "3.00", "base_price": "unit3"},
            {"product": "Zutaten für Suppe", "price": "", "base_price": "Rezept"},
        ],
        "nord_preview_discounts": [],
        "nord_valid_until": "18.7",
    }
    coordinator.data = mock_data
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)

    # 12 sensors should be created (6 for Süd, 6 for Nord)
    assert async_add_entities.called
    created_sensors = async_add_entities.call_args[0][0]
    assert len(created_sensors) == 12

    # Verify SÜD Current sensor (should filter out recipe)
    sued_current = created_sensors[0]
    assert sued_current._attr_name is None
    assert sued_current.device_info["name"] == "ALDI SÜD Offers"
    assert sued_current.native_value == 1
    assert sued_current.extra_state_attributes["discounts"] == [
        {"product": "Sued Product", "price": "1.00", "base_price": "unit"}
    ]
    assert sued_current.extra_state_attributes["valid_until"] == "13.7"
    assert sued_current.device_info["configuration_url"] == "https://sued-url"

    # Verify SÜD Recipes Current sensor (should contain only recipe, default disabled)
    sued_recipes = created_sensors[3]
    assert sued_recipes._attr_name == "Recipes"
    assert sued_recipes.entity_registry_enabled_default is False
    assert sued_recipes.native_value == 1
    assert sued_recipes.extra_state_attributes["discounts"] == [
        {
            "product": "Warme Melonensuppe",
            "price": "",
            "base_price": "Zutaten für 4 Portionen",
        }
    ]

    # Verify NORD Next sensor (should filter out recipe)
    nord_next = created_sensors[7]  # index 7 is AldiNordNextSensor
    assert nord_next._attr_name == "Next"
    assert nord_next.native_value == 1
    assert nord_next.extra_state_attributes["discounts"] == [
        {"product": "Nord Next Product", "price": "3.00", "base_price": "unit3"}
    ]
    assert nord_next.device_info["configuration_url"] == "https://nord-url"

    # Verify NORD Recipes Next sensor
    nord_recipes_next = created_sensors[10]  # index 10 is AldiNordRecipesNextSensor
    assert nord_recipes_next._attr_name == "Recipes Next"
    assert nord_recipes_next.entity_registry_enabled_default is False
    assert nord_recipes_next.native_value == 1
    assert nord_recipes_next.extra_state_attributes["discounts"] == [
        {"product": "Zutaten für Suppe", "price": "", "base_price": "Rezept"}
    ]


async def test_product_filter_sensor(hass: HomeAssistant) -> None:
    """Test AldiProductFilterSensor matching, best price calculation and attributes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_BOTH},
        options={"product_filters": ["Kaffee", "Schokolade"]},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.country = "de"
    coordinator.region = REGION_BOTH
    coordinator.product_filters = ["Kaffee", "Schokolade"]
    coordinator.sued_current_url = "https://sued-url"
    coordinator.nord_current_url = "https://nord-url"

    mock_data = {
        "discounts": [
            {
                "product": "Bio Kaffee Premium",
                "price": "4.49 €",
                "base_price": "500g (8.98/kg)",
                "category": "Kaffee & Tee",
                "picture_link": "https://img/kaffee1.png",
            },
            {
                "product": "Kaffee Mild",
                "price": "3.99 €",
                "base_price": "500g (7.98/kg)",
                "category": "Getränke",
                "picture_link": "https://img/kaffee2.png",
            },
            {
                "product": "Gouda Käse",
                "price": "1.99 €",
                "base_price": "400g",
                "category": "Molkerei",
                "picture_link": "https://img/gouda.png",
            },
        ],
        "valid_until": "13.7",
    }
    coordinator.data = mock_data
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)

    created_sensors = async_add_entities.call_args[0][0]
    # 12 standard sensors + 2 filter sensors
    assert len(created_sensors) == 14

    # Test Kaffee filter sensor (should match 2 items, best price 3.99 €)
    kaffee_sensor = created_sensors[12]
    assert isinstance(kaffee_sensor, AldiProductFilterSensor)
    assert kaffee_sensor.name == "Filter Kaffee"
    assert kaffee_sensor.native_value == "3.99 €"
    attrs = kaffee_sensor.extra_state_attributes
    assert attrs["filter"] == "Kaffee"
    assert attrs["on_sale"] is True
    assert attrs["match_count"] == 2
    assert attrs["best_price"] == "3.99 €"
    assert attrs["base_price"] == "500g (7.98/kg)"
    assert attrs["product_title"] == "Kaffee Mild"
    assert attrs["category"] == "Getränke"
    assert attrs["valid_until"] == "13.7"
    assert attrs["picture_link"] == "https://img/kaffee2.png"
    assert len(attrs["matches"]) == 2
    assert attrs["attribution"] == "Data provided by ALDI SÜD & NORD digital brochures"

    # Test Schokolade filter sensor (not on sale)
    schoko_sensor = created_sensors[13]
    assert isinstance(schoko_sensor, AldiProductFilterSensor)
    assert schoko_sensor.name == "Filter Schokolade"
    assert schoko_sensor.native_value == "Nicht im Angebot"
    schoko_attrs = schoko_sensor.extra_state_attributes
    assert schoko_attrs["filter"] == "Schokolade"
    assert schoko_attrs["on_sale"] is False
    assert schoko_attrs["match_count"] == 0
    assert schoko_attrs["best_price"] is None
    assert schoko_attrs["base_price"] is None
    assert schoko_attrs["product_title"] is None
    assert schoko_attrs["category"] is None
    assert schoko_attrs["picture_link"] is None
    assert schoko_attrs["matches"] == []
    assert (
        schoko_attrs["attribution"]
        == "Data provided by ALDI SÜD & NORD digital brochures"
    )
