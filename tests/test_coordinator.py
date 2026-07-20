"""Test the ALDI weekly offers coordinator."""

from unittest.mock import MagicMock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aldi.const import (
    DOMAIN,
    CONF_COUNTRY,
    CONF_REGION,
    REGION_SUED,
    REGION_NORD,
    COUNTRY_AT,
    COUNTRY_CH,
    COUNTRY_HU,
    COUNTRY_IT,
    COUNTRY_SI,
)
from custom_components.aldi.coordinator import AldiDataUpdateCoordinator

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_coordinator_fetch_sued_success(hass: HomeAssistant) -> None:
    """Test successful ALDI Süd offers fetch and parsing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_COUNTRY: "de", CONF_REGION: REGION_SUED},
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
                    "productType": "Obst & Gemüse",
                }
            ],
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
        assert (
            len(res["sued_discounts"]) == 3
        )  # 3 pages/spreads generated, each fetches hotspots
        assert res["sued_discounts"][0]["product"] == "Bananen"
        assert res["sued_discounts"][0]["price"] == "1.49"
        assert (
            res["sued_discounts"][0]["picture_link"]
            == "https://prospekt.aldi-sued.de/banana.png"
        )


async def test_coordinator_fetch_nord_success(hass: HomeAssistant) -> None:
    """Test successful ALDI Nord offers fetch and parsing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_COUNTRY: "de", CONF_REGION: REGION_NORD},
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
        data={CONF_COUNTRY: "de", CONF_REGION: REGION_SUED},
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


async def test_coordinator_fetch_international_success(hass: HomeAssistant) -> None:
    """Test successful fetch of international/AEM country flyers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_COUNTRY: COUNTRY_AT, CONF_REGION: COUNTRY_AT},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = AldiDataUpdateCoordinator(hass, entry)

    # Mock response data for CMS and hotspots
    current_week = dt_util.now().isocalendar().week
    cms_response = {
        "data": {
            "sitemap": [
                {
                    "link": {
                        "url": f"https://katalog.hofer.at/flipbook_kw{current_week}_26_0"
                    }
                }
            ]
        }
    }
    index_html = '{"numPages": 2}'
    hotspots_response = [
        {
            "type": "product",
            "products": [
                {
                    "title": "Kaffee",
                    "description": "Premium Kaffee",
                    "price": "4.99",
                    "discountedPrice": "3.99",
                    "photoUrls": [{"full": "/kaffee.png"}],
                    "productType": "Sortiment",
                }
            ],
        }
    ]

    async def mock_request_helper(session, url, return_json=True):
        if "flugblatt.content.v1.api" in url:
            return cms_response
        elif "hotspots_data.json" in url:
            return hotspots_response
        else:
            return index_html

    with (
        patch.object(coordinator, "_request", side_effect=mock_request_helper),
        patch("asyncio.sleep"),
    ):
        res = await coordinator._async_update_data()
        assert f"KW {current_week}" in res["sued_valid_until"]
        assert (
            len(res["sued_discounts"]) == 2
        )  # 2 pages spreads generated, fetches hotspots
        assert res["sued_discounts"][0]["product"] == "Kaffee"
        assert res["sued_discounts"][0]["price"] == "3.99"
        assert (
            res["sued_discounts"][0]["picture_link"]
            == "https://katalog.hofer.at/kaffee.png"
        )


async def test_coordinator_fetch_other_countries_success(hass: HomeAssistant) -> None:
    """Test successful flyer fetch for CH, HU, IT, SI."""
    current_week = dt_util.now().isocalendar().week

    # Test cases mapping country to expected URL pattern and test slug
    cases = [
        (
            COUNTRY_CH,
            "broschuere.content.v1.api",
            f"https://catalog.aldi-suisse.ch/aldiwoche_kw{current_week}-2026_de",
            "https://catalog.aldi-suisse.ch",
        ),
        (
            COUNTRY_HU,
            "online-akcios-ujsag.content.v1.api",
            f"https://szorolap.aldi.hu/aldi_online_akcios_ujsag_2026_07_23_kw{current_week}_r374zfuo",
            "https://szorolap.aldi.hu",
        ),
        (
            COUNTRY_IT,
            "volantino-online.content.v1.api",
            "https://volantino.aldi.it/ALDI_Offerte_da_lunedi_20_Luglio",
            "https://volantino.aldi.it",
        ),
        (
            COUNTRY_SI,
            "aktualni-letaki-in-brosure.content.v1.api",
            f"https://letaki.hofer.si/letak_kw{current_week}_2026_poletje",
            "https://letaki.hofer.si",
        ),
    ]

    for country, cms_endpoint, brochure_url, photo_prefix in cases:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_COUNTRY: country, CONF_REGION: country},
            options={},
        )
        entry.add_to_hass(hass)

        coordinator = AldiDataUpdateCoordinator(hass, entry)

        cms_response = {"data": {"sitemap": [{"link": {"url": brochure_url}}]}}
        # Italian date matching requires Luglio to be matched for week 30
        if country == COUNTRY_IT:
            # We override cms_response to match the Italian pattern
            cms_response = {
                "data": {
                    "sitemap": [
                        {
                            "link": {
                                "url": "https://volantino.aldi.it/ALDI_Offerte_da_lunedi_20_Luglio"
                            }
                        }
                    ]
                }
            }

        index_html = '{"numPages": 2}'
        hotspots_response = [
            {
                "type": "product",
                "products": [
                    {
                        "title": f"Product-{country}",
                        "description": "Desc",
                        "price": "2.99",
                        "discountedPrice": "1.99",
                        "photoUrls": [{"full": "/img.png"}],
                        "productType": "Type",
                    }
                ],
            }
        ]

        async def mock_request_helper(session, url, return_json=True):
            if cms_endpoint in url:
                return cms_response
            elif "hotspots_data.json" in url:
                return hotspots_response
            else:
                return index_html

        with (
            patch.object(coordinator, "_request", side_effect=mock_request_helper),
            patch("asyncio.sleep"),
        ):
            res = await coordinator._async_update_data()
            assert len(res["sued_discounts"]) == 2
            assert res["sued_discounts"][0]["product"] == f"Product-{country}"
            assert res["sued_discounts"][0]["price"] == "1.99"
            assert res["sued_discounts"][0]["picture_link"] == f"{photo_prefix}/img.png"

        # Cleanup config entry for next loop iteration
        await hass.config_entries.async_remove(entry.entry_id)
