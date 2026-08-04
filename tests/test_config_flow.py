"""Test the ALDI weekly offers config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import (
    CONF_COUNTRY,
    CONF_REGION,
    CONF_UPDATE_INTERVAL,
    COUNTRY_AT,
    COUNTRY_CH,
    COUNTRY_DE,
    COUNTRY_HU,
    COUNTRY_IT,
    COUNTRY_SI,
    DOMAIN,
    REGION_BOTH,
    REGION_SUED,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Mock setting up the config entry."""
    with patch(
        "custom_components.aldi.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


async def test_flow_user_setup_germany(hass: HomeAssistant) -> None:
    """Test Germany user setup step of the config flow going to region selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Select Germany
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: COUNTRY_DE},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "region"

    # Select Region
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION_SUED},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "ALDI SÜD Offers"
    assert result["data"] == {CONF_COUNTRY: COUNTRY_DE, CONF_REGION: REGION_SUED}


async def test_flow_user_setup_austria(hass: HomeAssistant) -> None:
    """Test Austria user setup step completing immediately."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Select Austria
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: COUNTRY_AT},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "HOFER Österreich Offers"
    assert result["data"] == {CONF_COUNTRY: COUNTRY_AT, CONF_REGION: COUNTRY_AT}


async def test_flow_already_configured(hass: HomeAssistant) -> None:
    """Test config flow aborts when the same region is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ALDI SÜD Offers",
        data={CONF_COUNTRY: COUNTRY_DE, CONF_REGION: REGION_SUED},
        unique_id=f"aldi_{REGION_SUED}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # Select Germany
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: COUNTRY_DE},
    )
    # Select Region -> should abort
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


async def test_flow_user_setup_other_countries(hass: HomeAssistant) -> None:
    """Test setup flow for other supported countries (CH, HU, IT, SI)."""
    for country, title in [
        (COUNTRY_CH, "ALDI Suisse Offers"),
        (COUNTRY_HU, "ALDI Magyarország Offers"),
        (COUNTRY_IT, "ALDI Italia Offers"),
        (COUNTRY_SI, "HOFER Slovenija Offers"),
    ]:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_COUNTRY: country},
        )
        assert result["type"] == "create_entry"
        assert result["title"] == title
        assert result["data"] == {CONF_COUNTRY: country, CONF_REGION: country}
