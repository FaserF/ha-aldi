"""Test ALDI diagnostics."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import CONF_REGION, DOMAIN, REGION_BOTH
from custom_components.aldi.diagnostics import async_get_config_entry_diagnostics

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_diagnostics(hass: HomeAssistant) -> None:
    """Test diagnostics returns expected structure."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ALDI SÜD & NORD Offers",
        data={CONF_REGION: REGION_BOTH},
        unique_id=f"aldi_{REGION_BOTH}",
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.region = REGION_BOTH
    coordinator.sued_current_url = "https://sued-url"
    coordinator.nord_current_url = "https://nord-url"
    coordinator._consecutive_failures = 0
    coordinator._last_success = None
    coordinator._backoff_until = None
    coordinator.data = {
        "sued_discounts": [{"product": "Bananen", "price": "1.49"}],
        "sued_next_discounts": [],
        "sued_preview_discounts": [],
        "nord_discounts": [],
        "nord_next_discounts": [],
        "nord_preview_discounts": [],
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["domain"] == DOMAIN
    assert result["entry"]["title"] == "ALDI SÜD & NORD Offers"
    assert result["coordinator"]["region"] == REGION_BOTH
    assert result["coordinator"]["sued_offers_count"] == 1
    assert result["coordinator"]["nord_offers_count"] == 0
    assert result["coordinator"]["has_data"] is True
    assert result["coordinator"]["last_success"] is None
    assert result["coordinator"]["backoff_until"] is None
