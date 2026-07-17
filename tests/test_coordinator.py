"""Test the ALDI weekly offers coordinator."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import DOMAIN, CONF_REGION, REGION_BOTH, REGION_SUED, REGION_NORD
from custom_components.aldi.coordinator import AldiDataUpdateCoordinator

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_coordinator_fetch_sued_success(hass: HomeAssistant) -> None:
    """Test successful ALDI Süd offers fetch and parsing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_SUED},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = AldiDataUpdateCoordinator(hass, entry)

    # Mock response data
    wrapper_response = {
        "kw29": {"slug": "kw29-slug", "valid_date": "13.7"},
        "kw30": {"slug": "kw30-slug", "valid_date": "20.7"},
        "kw31": {"slug": "kw31-slug", "valid_date": "27.7"},
    }
    index_html = '{"numPages": 4}'
    hotspots_response = [
        {
            "type": "product",
            "products": [
                {
                    "title": "Bananen",
                    "description": "Premium Bananen",
                    "price": "1.99",
                    "discountedPrice": "1.49",
                    "photoUrls": [{"full": "/banana.png"}],
                    "productType": "Obst & Gemüse"
                }
            ]
        }
    ]

    async def mock_request_helper(session, url, return_json=True):
        if "pub-by-week" in url:
            return wrapper_response
        elif "hotspots_data.json" in url:
            return hotspots_response
        else:
            return index_html

    with (
        patch.object(coordinator, "_request", side_effect=mock_request_helper),
        patch("asyncio.sleep"),
    ):
        res = await coordinator._async_update_data()
        assert res["sued_valid_until"] == "13.7"
        assert res["sued_next_valid_until"] == "20.7"
        assert res["sued_preview_valid_until"] == "27.7"
        assert len(res["sued_discounts"]) == 3 # 3 pages/spreads generated, each fetches hotspots
        assert res["sued_discounts"][0]["product"] == "Bananen"
        assert res["sued_discounts"][0]["price"] == "1.49"
        assert res["sued_discounts"][0]["picture_link"] == "https://prospekt.aldi-sued.de/banana.png"


async def test_coordinator_fetch_nord_success(hass: HomeAssistant) -> None:
    """Test successful ALDI Nord offers fetch and parsing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_NORD},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = AldiDataUpdateCoordinator(hass, entry)

    # Enrichments URL must contain "Enrichments" as the coordinator filters by that string
    enrichments_url = "https://ipaper.com/data/Enrichments.json"
    next_data_html = (
        '<script id="__NEXT_DATA__">{"props": {"pageProps": {"page": {"link": '
        '"https://magazine.aldi-nord.de/cw29/"}, "apiData": '
        '"[[\\"LEAFLET_IPAPER_STRUCTURE_GET\\",{\\"res\\":[{\\"pageNumber\\":\\"1\\",'
        '\\"url\\":\\"https://ipaper.com/1.png\\"}]}]]"}}}</script>'
    )
    # Magazine HTML must include pageTexts (parseable by the coordinator's regex) and an Enrichments URL
    magazine_html = (
        f'"pageTexts": ["Plattpfirsiche Paraguayos 1-kg-Schale 2. 22 ** 2.49"],'
        f' "{enrichments_url}"'
    )
    enrichments_json = {
        "enrichments": [
            {
                "type": 13,
                "name": "Plattpfirsiche Paraguayos",
                "pageIndex": 0,
            }
        ]
    }

    async def mock_request_helper(session, url, return_json=True):
        if "aldi-aktuell" in url or "aldi-vorschau" in url or "aldi-ausblick" in url:
            return next_data_html
        elif "Enrichments" in url:
            return enrichments_json
        else:
            # magazine page
            return magazine_html

    with (
        patch.object(coordinator, "_request", side_effect=mock_request_helper),
        patch("asyncio.sleep"),
    ):
        res = await coordinator._async_update_data()
        assert len(res["nord_discounts"]) == 1
        assert res["nord_discounts"][0]["product"] == "Plattpfirsiche Paraguayos"
        assert res["nord_discounts"][0]["price"] == "2.22"
        assert res["nord_discounts"][0]["picture_link"] == "https://ipaper.com/1.png"


async def test_coordinator_backoff_on_blocking(hass: HomeAssistant) -> None:
    """Test that coordinator correctly triggers back-off on 403 or 429 response codes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: REGION_SUED},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = AldiDataUpdateCoordinator(hass, entry)

    mock_resp = MagicMock()
    mock_resp.status = 403

    # Setup mock ClientSession.get returning 403
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    with pytest.raises(UpdateFailed):
        await coordinator._request(mock_session, "https://url")

    # Verify backoff is active
    assert coordinator._consecutive_failures == 1
    assert coordinator._backoff_until is not None
    assert coordinator._backoff_until > dt_util.now()

    # Subsequent requests within backoff time should immediately fail/skip
    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._request(mock_session, "https://url")
    assert "skipped due to active back-off" in str(exc_info.value)
