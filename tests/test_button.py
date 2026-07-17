"""Test the ALDI weekly offers force-update buttons."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import DOMAIN, CONF_REGION, REGION_BOTH, REGION_SUED, REGION_NORD
from custom_components.aldi.button import async_setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_buttons_created_for_both(hass: HomeAssistant) -> None:
    """Test that two Force Update buttons are created when region is 'both'."""
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
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)

    created = async_add_entities.call_args[0][0]
    assert len(created) == 2
    names = {b.name for b in created}
    assert "ALDI SÜD Force Update" in names
    assert "ALDI NORD Force Update" in names


async def test_buttons_created_for_sued_only(hass: HomeAssistant) -> None:
    """Test that only one Force Update button is created for Süd-only config."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_SUED},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.region = REGION_SUED
    coordinator.sued_current_url = "https://sued-url"
    coordinator.nord_current_url = ""
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)

    created = async_add_entities.call_args[0][0]
    assert len(created) == 1
    assert created[0].name == "ALDI SÜD Force Update"


async def test_button_press_triggers_refresh(hass: HomeAssistant) -> None:
    """Test that pressing the button calls async_request_refresh on the coordinator."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_NORD},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.region = REGION_NORD
    coordinator.sued_current_url = ""
    coordinator.nord_current_url = "https://nord-url"
    coordinator.async_request_refresh = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    button = async_add_entities.call_args[0][0][0]

    await button.async_press()
    coordinator.async_request_refresh.assert_awaited_once()
