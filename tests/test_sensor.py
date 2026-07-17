"""Test the ALDI weekly offers sensors."""

from unittest.mock import MagicMock
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import DOMAIN, CONF_REGION, REGION_BOTH
from custom_components.aldi.sensor import async_setup_entry

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
    coordinator.region = REGION_BOTH
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
    assert sued_current.name == "ALDI SÜD Offers"
    assert sued_current.native_value == 1
    assert sued_current.extra_state_attributes["discounts"] == [
        {"product": "Sued Product", "price": "1.00", "base_price": "unit"}
    ]
    assert sued_current.extra_state_attributes["valid_until"] == "13.7"
    assert sued_current.device_info["configuration_url"] == "https://sued-url"

    # Verify SÜD Recipes Current sensor (should contain only recipe, default disabled)
    sued_recipes = created_sensors[3]
    assert sued_recipes.name == "ALDI SÜD Recipes"
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
    assert nord_next.name == "ALDI NORD Offers Next"
    assert nord_next.native_value == 1
    assert nord_next.extra_state_attributes["discounts"] == [
        {"product": "Nord Next Product", "price": "3.00", "base_price": "unit3"}
    ]
    assert nord_next.device_info["configuration_url"] == "https://nord-url"

    # Verify NORD Recipes Next sensor
    nord_recipes_next = created_sensors[10]  # index 10 is AldiNordRecipesNextSensor
    assert nord_recipes_next.name == "ALDI NORD Recipes Next"
    assert nord_recipes_next.entity_registry_enabled_default is False
    assert nord_recipes_next.native_value == 1
    assert nord_recipes_next.extra_state_attributes["discounts"] == [
        {"product": "Zutaten für Suppe", "price": "", "base_price": "Rezept"}
    ]
