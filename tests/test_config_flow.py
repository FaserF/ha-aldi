"""Test the ALDI weekly offers config flow."""

from unittest.mock import patch
import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.aldi.const import DOMAIN, CONF_REGION, REGION_BOTH, REGION_SUED, CONF_UPDATE_INTERVAL

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_flow_user_setup(hass: HomeAssistant) -> None:
    """Test user setup step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION_SUED},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "ALDI SÜD Offers"
    assert result["data"] == {CONF_REGION: REGION_SUED}


async def test_flow_already_configured(hass: HomeAssistant) -> None:
    """Test config flow aborts when the same region is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ALDI SÜD Offers",
        data={CONF_REGION: REGION_SUED},
        unique_id=f"aldi_{REGION_SUED}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION_SUED},
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow to configure update interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ALDI SÜD & NORD Offers",
        data={CONF_REGION: REGION_BOTH},
        unique_id=f"aldi_{REGION_BOTH}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 6},
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {CONF_UPDATE_INTERVAL: 6}
