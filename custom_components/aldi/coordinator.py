"""Data Update Coordinator for the ALDI weekly offers integration."""

from __future__ import annotations

import asyncio
import datetime
import logging
import re
import json
import random
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BASE_PRICE,
    ATTR_CATEGORY,
    ATTR_DISCOUNT_PRICE,
    ATTR_DISCOUNT_TITLE,
    ATTR_PICTURE,
    CONF_COUNTRY,
    CONF_REGION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
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

_LOGGER = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
]


def get_random_headers() -> dict[str, str]:
    """Generate random headers to mimic a real browser and avoid IP bans."""
    ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    if "Chrome" in ua:
        headers["Sec-CH-UA"] = (
            '"Google Chrome";v="148", "Chromium";v="148", "Not=A?Brand";v="99"'
        )
        headers["Sec-CH-UA-Mobile"] = "?0"
        headers["Sec-CH-UA-Platform"] = '"Windows"' if "Windows" in ua else '"macOS"'

    return headers


class AldiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage fetching ALDI weekly offer data."""

    config_entry: config_entries.ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
        """Initialize the coordinator."""
        config = {**entry.data, **entry.options}
        self.region: str = config[CONF_REGION]
        self.country: str = config.get(CONF_COUNTRY, COUNTRY_DE)
        self.config_entry = entry

        self.store: storage.Store = storage.Store(hass, 1, f"{DOMAIN}_{self.region}")
        self._last_success: datetime.datetime | None = None
        self._backoff_until: datetime.datetime | None = None
        self._consecutive_failures = 0

        self.sued_current_url = "https://prospekt.aldi-sued.de/"
        self.nord_current_url = "https://www.aldi-nord.de/prospekte.html"

        # CMS URLs and regex patterns for international countries (all using AEM and Publitas)
        self.country_configs = {
            COUNTRY_AT: {
                "cms_url": "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/at/web/main/de/flugblatt.content.v1.api/content.json",
                "url_pattern": r"https://katalog\.hofer\.at/flipbook_kw[0-9]+_[0-9]+_[0-9]+",
                "default_url": "https://katalog.hofer.at/",
            },
            COUNTRY_CH: {
                "cms_url": "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/ch/web/main/de/broschuere.content.v1.api/content.json",
                "url_pattern": r"https://catalog\.aldi-suisse\.ch/aldiwoche_kw[0-9]+-[0-9]+_[a-z]+",
                "default_url": "https://www.aldi-suisse.ch/de/broschuere.html",
            },
            COUNTRY_HU: {
                "cms_url": "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/hu/web/main/hu/online-akcios-ujsag.content.v1.api/content.json",
                "url_pattern": r"https://szorolap\.aldi\.hu/[a-zA-Z0-9_]+",
                "default_url": "https://www.aldi.hu/hu/akciok/online-szorolap.html",
            },
            COUNTRY_IT: {
                "cms_url": "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/it/web/main/it/volantino-online.content.v1.api/content.json",
                "url_pattern": r"https://volantino\.aldi\.it/[a-zA-Z0-9_]+",
                "default_url": "https://www.aldi.it/it/offerte/volantino-online.html",
            },
            COUNTRY_SI: {
                "cms_url": "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/si/web/main/sl/aktualni-letaki-in-brosure.content.v1.api/content.json",
                "url_pattern": r"https://letaki\.hofer\.si/[a-zA-Z0-9_]+",
                "default_url": "https://www.hofer.si/sl/aktualni-letaki-in-brosure.html",
            },
        }

        interval_hours = config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"ALDI {self.region} Coordinator",
            update_interval=datetime.timedelta(hours=interval_hours),
        )

    async def async_load_cache(self) -> None:
        """Load cached data from storage."""
        cache = await self.store.async_load()
        if cache:
            self.data = cache
            if "last_success" in cache:
                try:
                    self._last_success = dt_util.parse_datetime(cache["last_success"])
                except (ValueError, TypeError):
                    self._last_success = None
            if "sued_current_url" in cache:
                self.sued_current_url = cache["sued_current_url"]
            if "nord_current_url" in cache:
                self.nord_current_url = cache["nord_current_url"]

    async def _request(
        self, session: aiohttp.ClientSession, url: str, return_json: bool = True
    ) -> Any:
        """Perform request with random headers, anti-ban lock, and consecutive backoffs."""
        if self._backoff_until and dt_util.now() < self._backoff_until:
            _LOGGER.warning(
                "Request to %s skipped due to active back-off until %s",
                url,
                self._backoff_until,
            )
            raise UpdateFailed(
                f"Request skipped due to active back-off until {self._backoff_until}"
            )

        headers = get_random_headers()
        try:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in (403, 429):
                    self._consecutive_failures += 1
                    backoff_hours = min(24, self._consecutive_failures * 2)
                    self._backoff_until = dt_util.now() + datetime.timedelta(
                        hours=backoff_hours
                    )
                    _LOGGER.error(
                        "Received %s (Blocked) for %s. Backing off for %d hours",
                        response.status,
                        url,
                        backoff_hours,
                    )
                    raise UpdateFailed(f"Access blocked ({response.status})")

                if response.status != 200:
                    self._consecutive_failures += 1
                    backoff_mins = min(1440, self._consecutive_failures * 60)
                    self._backoff_until = dt_util.now() + datetime.timedelta(
                        minutes=backoff_mins
                    )
                    _LOGGER.warning(
                        "HTTP %s for %s. Backing off for %d minutes",
                        response.status,
                        url,
                        backoff_mins,
                    )
                    raise UpdateFailed(f"HTTP error {response.status}")

                # Success
                self._consecutive_failures = 0
                self._backoff_until = None

                if return_json:
                    return await response.json()
                return await response.text()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            self._consecutive_failures += 1
            backoff_mins = min(1440, self._consecutive_failures * 60)
            self._backoff_until = dt_util.now() + datetime.timedelta(
                minutes=backoff_mins
            )
            _LOGGER.warning(
                "Connection error for %s: %s. Backing off for %d minutes",
                url,
                err,
                backoff_mins,
            )
            raise UpdateFailed(f"Connection error: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and parse new data from ALDI."""
        # Anti-ban lock
        domain_data = self.hass.data.setdefault(DOMAIN, {})
        fetch_lock: asyncio.Lock = domain_data.setdefault("fetch_lock", asyncio.Lock())

        async with fetch_lock:
            # Random jitter to prevent strict rate limiting
            await asyncio.sleep(random.uniform(5.0, 15.0))

            async with aiohttp.ClientSession() as session:
                data: dict[str, Any] = {}

                # International (AT, CH, HU, IT, SI)
                if self.country != COUNTRY_DE:
                    try:
                        country_data = await self._fetch_publitas_country_data(session)
                        data.update(country_data)
                    except Exception as err:
                        _LOGGER.error(
                            "Failed to fetch international ALDI data for %s: %s",
                            self.country,
                            err,
                        )
                        raise UpdateFailed(
                            f"Failed to fetch international ALDI: {err}"
                        ) from err
                else:
                    # Germany ALDI Süd
                    if self.region in (REGION_SUED, REGION_BOTH):
                        try:
                            sued_data = await self._fetch_sued_data(session)
                            data.update(sued_data)
                        except Exception as err:
                            _LOGGER.error("Failed to fetch ALDI SÜD data: %s", err)
                            if self.region == REGION_SUED:
                                raise UpdateFailed(
                                    f"Failed to fetch ALDI SÜD: {err}"
                                ) from err

                    # Germany ALDI Nord
                    if self.region in (REGION_NORD, REGION_BOTH):
                        try:
                            nord_data = await self._fetch_nord_data(session)
                            data.update(nord_data)
                        except Exception as err:
                            _LOGGER.error("Failed to fetch ALDI NORD data: %s", err)
                            if self.region == REGION_NORD:
                                raise UpdateFailed(
                                    f"Failed to fetch ALDI NORD: {err}"
                                ) from err

                self._last_success = dt_util.now()
                data["last_success"] = self._last_success.isoformat()
                data["sued_current_url"] = self.sued_current_url
                data["nord_current_url"] = self.nord_current_url
                await self.store.async_save(data)
                return data

    def parse_week_from_url(self, url: str) -> int | None:
        """Parse the calendar week number from a brochure/flyer URL."""
        # 1. Match kwXX pattern (e.g. kw30 or kw_30 or kw-30)
        match = re.search(r"kw_?[-]?(\d+)", url, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # 2. Match Italian date pattern da_lunedi_DD_Month
        match_it = re.search(r"da_lunedi_(\d+)_([A-Za-z]+)", url, re.IGNORECASE)
        if match_it:
            day = int(match_it.group(1))
            month_name = match_it.group(2).lower()
            months = {
                "gennaio": 1,
                "febbraio": 2,
                "marzo": 3,
                "aprile": 4,
                "maggio": 5,
                "giugno": 6,
                "luglio": 7,
                "agosto": 8,
                "settembre": 9,
                "ottobre": 10,
                "novembre": 11,
                "dicembre": 12,
            }
            month = months.get(month_name)
            if month:
                today = datetime.date.today()
                year = today.year
                # Rollover handling
                if today.month == 12 and month == 1:
                    year += 1
                elif today.month == 1 and month == 12:
                    year -= 1
                try:
                    d = datetime.date(year, month, day)
                    return d.isocalendar().week
                except ValueError:
                    pass
        return None

    async def _fetch_nuxt_offers(
        self, session: aiohttp.ClientSession, url: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch and parse weekly offers from Nuxt hydration state."""
        try:
            html = await self._request(session, url, return_json=False)
            scripts = re.findall(
                r"<script[^>]*>(.*?)</script\s*[^>]*>", html, re.DOTALL | re.IGNORECASE
            )
            payload_script = None
            for s in scripts:
                if s.strip().startswith("[") and "i18nResult" in s:
                    payload_script = s.strip()
                    break

            if not payload_script:
                _LOGGER.debug("No Nuxt hydration script found on %s", url)
                return {}

            data_list = json.loads(payload_script)

            def decode_val(val: Any, memo: dict[int, Any] | None = None) -> Any:
                if memo is None:
                    memo = {}
                if isinstance(val, int) and not isinstance(val, bool):
                    if 0 <= val < len(data_list):
                        if val in memo:
                            return memo[val]
                        raw = data_list[val]
                        if isinstance(raw, dict):
                            res_dict: dict[str, Any] = {}
                            memo[val] = res_dict
                            for k, v in raw.items():
                                res_dict[k] = decode_val(v, memo)
                            return res_dict
                        elif isinstance(raw, list):
                            if (
                                len(raw) == 2
                                and isinstance(raw[0], str)
                                and raw[0] in ("ShallowReactive", "Reactive", "Ref")
                            ):
                                res_val = decode_val(raw[1], memo)
                                memo[val] = res_val
                                return res_val
                            res_list: list[Any] = []
                            memo[val] = res_list
                            for v in raw:
                                res_list.append(decode_val(v, memo))
                            return res_list
                        else:
                            memo[val] = raw
                            return raw
                return val

            root = decode_val(1)
            state = root.get("state", {}) if isinstance(root, dict) else {}

            all_products = []
            for k, v in state.items():
                if (
                    isinstance(v, list)
                    and len(v) > 0
                    and isinstance(v[0], dict)
                    and "sku" in v[0]
                ):
                    for item in v:
                        if "name" in item and "price" in item and item["price"]:
                            all_products.append(item)

            current_week = datetime.date.today().isocalendar().week
            next_week = (current_week + 1) if current_week < 52 else 1
            preview_week = (next_week + 1) if next_week < 52 else 1

            classified: dict[str, list[dict[str, Any]]] = {
                "current": [],
                "next": [],
                "preview": [],
            }

            for p in all_products:
                title = p["name"]
                if p.get("brandName"):
                    title = f"{p['brandName']} {title}"

                price_info = p.get("price") or {}
                price = price_info.get("amountRelevantDisplay")
                if not price and price_info.get("amount"):
                    price = f"€ {price_info['amount'] / 100:.2f}"
                if not price:
                    price = ""

                desc = p.get("sellingSize") or ""

                photo_url = ""
                assets = p.get("assets") or []
                if assets and isinstance(assets, list):
                    photo_url = assets[0].get("url") or ""
                    if photo_url and "{width}" in photo_url:
                        photo_url = photo_url.replace("{width}", "800").replace(
                            "{slug}", p.get("urlSlugText", "")
                        )

                prod_data = {
                    ATTR_DISCOUNT_TITLE: title,
                    ATTR_DISCOUNT_PRICE: price,
                    ATTR_BASE_PRICE: desc,
                    ATTR_PICTURE: photo_url,
                    ATTR_CATEGORY: "Angebote",
                }

                sale_date_str = p.get("onSaleDateDisplay") or ""
                date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", sale_date_str)
                week = None
                if date_match:
                    day, month, year = map(int, date_match.groups())
                    try:
                        d = datetime.date(year, month, day)
                        week = d.isocalendar().week
                    except ValueError:
                        pass

                if week == current_week:
                    classified["current"].append(prod_data)
                elif week == next_week:
                    classified["next"].append(prod_data)
                elif week == preview_week:
                    classified["preview"].append(prod_data)
                else:
                    classified["current"].append(prod_data)

            return classified
        except Exception as e:
            _LOGGER.warning("Failed to parse Nuxt offers: %s", e)
            return {}

    async def _fetch_publitas_country_data(
        self, session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Fetch and parse flyer data for international Publitas/AEM countries."""
        config = self.country_configs[self.country]
        _LOGGER.debug(
            "Fetching ALDI/HOFER data for %s from %s", self.country, config["cms_url"]
        )

        # 1. Fetch CMS sitemap or content JSON containing active brochures
        cms_json = await self._request(session, config["cms_url"], return_json=True)
        text_content = json.dumps(cms_json)

        # 2. Find matching brochure URLs
        urls = re.findall(config["url_pattern"], text_content)
        if not urls:
            _LOGGER.warning(
                "No brochure URLs found for %s, falling back to empty list",
                self.country,
            )
            return {
                "sued_discounts": [],
                "sued_next_discounts": [],
                "sued_preview_discounts": [],
                "sued_valid_until": "",
                "sued_next_valid_until": "",
                "sued_preview_valid_until": "",
            }

        # 3. Group base URLs by calendar week
        by_week: dict[int, list[str]] = {}
        for raw_url in urls:
            # Strip suffix /page/1 or /
            base_url = re.sub(r"/(?:page/\d+|)$", "", raw_url)
            if "\\u" in base_url:
                base_url = base_url.encode().decode("unicode_escape")
            week = self.parse_week_from_url(base_url)
            if week is not None:
                by_week.setdefault(week, []).append(base_url)

        # 4. Resolve Current, Next, and Preview weeks
        current_week = datetime.date.today().isocalendar().week
        next_week = (current_week + 1) if current_week < 52 else 1
        preview_week = (next_week + 1) if next_week < 52 else 1

        current_urls = by_week.get(current_week, [])
        next_urls = by_week.get(next_week, [])
        preview_urls = by_week.get(preview_week, [])

        # Fallback if current week is missing but we have other weeks
        if not current_urls and by_week:
            available_weeks = sorted(by_week.keys())
            current_week = available_weeks[0]
            current_urls = by_week[current_week]
            next_week = (
                available_weeks[1] if len(available_weeks) > 1 else current_week + 1
            )
            next_urls = by_week.get(next_week, [])
            preview_week = (
                available_weeks[2] if len(available_weeks) > 2 else next_week + 1
            )
            preview_urls = by_week.get(preview_week, [])

        if current_urls:
            self.sued_current_url = current_urls[0]
        else:
            self.sued_current_url = config["default_url"]

        # 5. Fetch and merge discounts for all booklets in each week
        async def fetch_merged(urls_list: list[str]) -> list[dict[str, Any]]:
            merged = []
            for u in urls_list:
                try:
                    disc = await self._fetch_sued_leaflet(session, u)
                    merged.extend(disc)
                except Exception as e:
                    _LOGGER.warning("Failed to parse leaflet %s: %s", u, e)
            return merged

        current_discounts = await fetch_merged(current_urls)
        next_discounts = await fetch_merged(next_urls)
        preview_discounts = await fetch_merged(preview_urls)

        # Merge Nuxt offers for Austria and Hungary
        if self.country in (COUNTRY_AT, COUNTRY_HU):
            nuxt_url = (
                "https://www.hofer.at/angebote"
                if self.country == COUNTRY_AT
                else "https://www.aldi.hu/hu/akciok"
            )
            nuxt_data = await self._fetch_nuxt_offers(session, nuxt_url)
            if nuxt_data:
                if nuxt_data.get("current"):
                    current_discounts.extend(nuxt_data["current"])
                if nuxt_data.get("next"):
                    next_discounts.extend(nuxt_data["next"])
                if nuxt_data.get("preview"):
                    preview_discounts.extend(nuxt_data["preview"])

        return {
            "sued_discounts": current_discounts,
            "sued_next_discounts": next_discounts,
            "sued_preview_discounts": preview_discounts,
            "sued_valid_until": f"KW {current_week}",
            "sued_next_valid_until": f"KW {next_week}" if next_urls else "",
            "sued_preview_valid_until": f"KW {preview_week}" if preview_urls else "",
        }

    async def _fetch_sued_data(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Fetch weekly offer data for ALDI Süd."""
        _LOGGER.debug("Fetching ALDI SÜD data")
        current_week = datetime.date.today().isocalendar().week

        # 1. Fetch publication wrapper
        url = f"https://services.publitas.com/aldi-sud/api-wrapper/pub-by-week?week={current_week}"
        wrapper = await self._request(session, url, return_json=True)

        # Find current and next weeks' slugs
        sorted_weeks = sorted(wrapper.keys())
        if not sorted_weeks:
            raise UpdateFailed("No SÜD weekly brochures found in API response")

        current_slug = wrapper[sorted_weeks[0]]["slug"]
        current_valid_until = wrapper[sorted_weeks[0]].get("valid_date", "")
        self.sued_current_url = f"https://prospekt.aldi-sued.de/{current_slug}/"

        next_slug = None
        next_valid_until = ""
        if len(sorted_weeks) > 1:
            next_slug = wrapper[sorted_weeks[1]]["slug"]
            next_valid_until = wrapper[sorted_weeks[1]].get("valid_date", "")

        preview_slug = None
        preview_valid_until = ""
        if len(sorted_weeks) > 2:
            preview_slug = wrapper[sorted_weeks[2]]["slug"]
            preview_valid_until = wrapper[sorted_weeks[2]].get("valid_date", "")

        # Fetch actual offers
        discounts = await self._fetch_sued_leaflet(session, current_slug)
        next_discounts = []
        if next_slug:
            next_discounts = await self._fetch_sued_leaflet(session, next_slug)
        preview_discounts = []
        if preview_slug:
            preview_discounts = await self._fetch_sued_leaflet(session, preview_slug)

        return {
            "sued_discounts": discounts,
            "sued_next_discounts": next_discounts,
            "sued_preview_discounts": preview_discounts,
            "sued_valid_until": current_valid_until,
            "sued_next_valid_until": next_valid_until,
            "sued_preview_valid_until": preview_valid_until,
        }

    async def _fetch_sued_leaflet(
        self, session: aiohttp.ClientSession, slug: str
    ) -> list[dict[str, Any]]:
        """Fetch all page spreads and extract products for a given ALDI Süd brochure slug or full URL."""
        if slug.startswith("http://") or slug.startswith("https://"):
            base_url = slug.rstrip("/")
        else:
            base_url = f"https://prospekt.aldi-sued.de/{slug}"

        html = await self._request(session, base_url, return_json=False)

        num_pages_match = re.search(r'"numPages"\s*:\s*(\d+)', html)
        if not num_pages_match:
            return []
        num_pages = int(num_pages_match.group(1))

        # Generate list of spreads
        pages = ["1"]
        for i in range(2, num_pages, 2):
            if i == num_pages:
                pages.append(str(i))
            else:
                pages.append(f"{i}-{i + 1}")
        if num_pages % 2 == 0 and num_pages > 1:
            pages.append(str(num_pages))

        # Fetch each hotspots_data.json
        discounts = []
        for page in pages:
            page_url = f"{base_url}/page/{page}/hotspots_data.json"
            try:
                hotspots = await self._request(session, page_url, return_json=True)
                for h in hotspots:
                    if h.get("type") == "product":
                        for prod in h.get("products", []):
                            title = prod.get("title", "")
                            desc = prod.get("description", "")
                            orig_price = prod.get("price", "")
                            disc_price = prod.get("discountedPrice") or orig_price

                            photo_url = ""
                            photos = prod.get("photoUrls", [])
                            if photos:
                                photo_url = (
                                    photos[0].get("full")
                                    or photos[0].get("thumb")
                                    or ""
                                )
                            if photo_url.startswith("/"):
                                # Parse domain/scheme from base_url to prefix absolute path photo URLs
                                domain_match = re.match(r"(https?://[^/]+)", base_url)
                                photo_prefix = (
                                    domain_match.group(1)
                                    if domain_match
                                    else "https://prospekt.aldi-sued.de"
                                )
                                photo_url = f"{photo_prefix}{photo_url}"

                            discounts.append(
                                {
                                    ATTR_DISCOUNT_TITLE: title,
                                    ATTR_DISCOUNT_PRICE: disc_price,
                                    ATTR_BASE_PRICE: f"{desc} (orig: {orig_price})"
                                    if orig_price
                                    else desc,
                                    ATTR_PICTURE: photo_url,
                                    ATTR_CATEGORY: prod.get("productType", "Angebote"),
                                }
                            )
            except Exception as e:
                _LOGGER.warning("Failed to fetch SÜD hotspots page %s: %s", page, e)
                continue
        return discounts

    async def _fetch_nord_data(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Fetch weekly offer data for ALDI Nord."""
        _LOGGER.debug("Fetching ALDI NORD data")

        current_data = await self._fetch_nord_leaflet(
            session, "https://www.aldi-nord.de/prospekte/aldi-aktuell.html"
        )
        if current_data.get("mag_url"):
            self.nord_current_url = current_data["mag_url"]

        next_data = await self._fetch_nord_leaflet(
            session, "https://www.aldi-nord.de/prospekte/aldi-vorschau.html"
        )

        preview_data = await self._fetch_nord_leaflet(
            session, "https://www.aldi-nord.de/prospekte/aldi-ausblick.html"
        )

        return {
            "nord_discounts": current_data.get("discounts", []),
            "nord_valid_until": current_data.get("valid_until", ""),
            "nord_next_discounts": next_data.get("discounts", []),
            "nord_next_valid_until": next_data.get("valid_until", ""),
            "nord_preview_discounts": preview_data.get("discounts", []),
            "nord_preview_valid_until": preview_data.get("valid_until", ""),
        }

    async def _fetch_nord_leaflet(
        self, session: aiohttp.ClientSession, entry_url: str
    ) -> dict[str, Any]:
        """Fetch and parse a single ALDI Nord brochure page."""
        html = await self._request(session, entry_url, return_json=False)

        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if not match:
            return {}

        next_data = json.loads(match.group(1))
        page_props = next_data.get("props", {}).get("pageProps", {})
        page = page_props.get("page", {})
        mag_url = page.get("link")
        if not mag_url:
            return {}

        # Extract page images mapping
        api_data_str = page_props.get("apiData", "[]")
        page_images = {}
        try:
            api_data = json.loads(api_data_str)
            if api_data and len(api_data) > 0 and len(api_data[0]) > 1:
                structure = api_data[0][1].get("res", [])
                for p_img in structure:
                    p_num = p_img.get("pageNumber")
                    p_url = p_img.get("url")
                    if p_num and p_url:
                        page_images[int(p_num) - 1] = p_url
        except Exception as e:
            _LOGGER.debug("Could not parse ALDI Nord page image maps: %s", e)

        # 2. Fetch the magazine HTML page
        mag_html = await self._request(session, mag_url, return_json=False)

        # Extract pageTexts
        match_texts = re.search(r'"pageTexts"\s*:\s*(\[.*?\]),', mag_html)
        if not match_texts:
            return {}
        page_texts = json.loads(match_texts.group(1))

        # Extract enrichment JSON URLs
        json_urls = re.findall(r"(https?://[^\s\"']+\.json[^\s\"']*)", mag_html)
        json_urls = [u.replace("\\u0026", "&") for u in json_urls if "Enrichments" in u]

        # 3. Load all product hotspots (type 13)
        all_type13 = []
        for jurl in json_urls:
            try:
                jdata = await self._request(session, jurl, return_json=True)
                all_type13.extend(
                    [e for e in jdata.get("enrichments", []) if e.get("type") == 13]
                )
            except Exception as e:
                _LOGGER.warning("Failed to fetch NORD enrichment JSON %s: %s", jurl, e)
                continue

        # Group products by pageIndex
        by_page: dict[int, list[dict[str, Any]]] = {}
        for p in all_type13:
            pidx = p.get("pageIndex")
            by_page.setdefault(pidx, []).append(p)

        discounts = []

        # 4. Perform window-based lenient matching on pageTexts
        def make_lenient_regex(name: str) -> str:
            clean = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß]", "", name)
            pattern = r""
            for char in clean:
                pattern += re.escape(char) + r"[\s\u00ad\u2009-]*"
            return pattern

        def _infer_nord_category(enrichment: dict[str, Any], window: str) -> str:
            """Return a category string for an ALDI NORD enrichment item.

            Tier 1 – field from the enrichment JSON (future-proof if ALDI ever
                      adds explicit category data to their API).
            Tier 2 – keyword matching on the surrounding page-text window.
            Tier 3 – fallback 'Angebote'.
            """
            # Tier 1: explicit field in enrichment object
            for field in ("category", "productType", "productCategory", "type_label"):
                val = enrichment.get(field)
                if val and isinstance(val, str) and val not in {"product", "13"}:
                    return val.strip()

            # Tier 2: keyword matching (case-insensitive, longest match wins)
            _KEYWORD_CATEGORIES: list[tuple[str, str]] = [
                # Food – fresh
                (
                    r"obst|gem[üu]se|salat|apfel|tomate|gurke|paprika|zitrone|orange|banane|erdbeere",
                    "Obst & Gemüse",
                ),
                (
                    r"fleisch|wurst|aufschnitt|schinken|salami|hackfleisch|steak|schnitzel|h[äa]hnchen|gefl[üu]gel",
                    "Fleisch & Wurst",
                ),
                (
                    r"fisch|lachs|forelle|thunfisch|garnele|meeresfrüchte",
                    "Fisch & Meeresfrüchte",
                ),
                (
                    r"milch|k[äa]se|joghurt|quark|sahne|butter|mozzarella",
                    "Milch & Käse",
                ),
                (
                    r"brot|br[öo]tchen|toast|backwaren|kuchen|keks|geb[äa]ck",
                    "Brot & Backwaren",
                ),
                (
                    r"tiefk[üu]hl|tk-|tiefgek[üu]hlt|pizza|eis(becher|würfel|creme)?",
                    "Tiefkühl",
                ),
                # Beverages
                (
                    r"getr[äa]nk|wasser|saft|limo|cola|bier|wein|sekt|kaffee|tee|kakao",
                    "Getränke",
                ),
                # Pantry
                (
                    r"nudel|pasta|reis|mehl|zucker|[öo]l|essig|soße|sauce|gew[üu]rz|mayonnaise|ketchup|senf",
                    "Vorrat",
                ),
                (
                    r"müsli|cornflakes|fr[üu]hst[üu]ck|marmelade|honig|aufstrich",
                    "Frühstück",
                ),
                (
                    r"schokolade|s[üu][ßs]igkeiten|bonbon|gummi|chips|snack|popcorn|n[üu]sse",
                    "Süßwaren & Snacks",
                ),
                (r"babynahrung|windel|baby", "Baby"),
                (
                    r"tiernahrung|hundefutter|katzenfutter|tierfutter|streu",
                    "Tierbedarf",
                ),
                # Non-food
                (
                    r"waschmittel|spülmittel|reiniger|putzmittel|hygiene",
                    "Haushalt & Reinigung",
                ),
                (
                    r"shampoo|duschgel|deo|seife|kosmetik|creme|pflege|zahnb[üu]rste|zahnpasta",
                    "Körperpflege",
                ),
                (
                    r"werkzeug|bohrer|s[äa]ge|hammer|schraube|klebeband|akku",
                    "Werkzeug & Baumarkt",
                ),
                (r"garten|pflanze|erde|d[üu]nger|blume|balkon|terrasse", "Garten"),
                (
                    r"textil|t-shirt|hose|jacke|socken|unterw[äa]sche|schuh|kleidung",
                    "Textilien",
                ),
                (
                    r"elektronik|handy|smartphone|tablet|laptop|kopfh[öo]rer|ladekabel|usb|hdmi",
                    "Elektronik",
                ),
                (r"spielzeug|lego|puppe|brettspiel|spiel", "Spielzeug"),
                (
                    r"sport|fitness|fahrrad|helm|camping|outdoor|rucksack",
                    "Sport & Freizeit",
                ),
            ]
            w_lower = window.lower()
            for pattern, label in _KEYWORD_CATEGORIES:
                if re.search(pattern, w_lower):
                    return label

            # Tier 3: fallback
            return "Angebote"

        for pidx, products in sorted(by_page.items()):
            if pidx >= len(page_texts):
                continue
            text = page_texts[pidx]

            positions = []
            for p in products:
                name = p.get("name", "")
                clean_name = name.replace("\u00ad", "").strip()
                clean_text = text.replace("\u00ad", "")

                pattern = make_lenient_regex(clean_name)
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    positions.append((match.start(), p, clean_name))

            positions.sort(key=lambda x: x[0])

            for idx, (pos, p, clean_name) in enumerate(positions):
                end_pos = (
                    positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
                )
                window_text = text[pos:end_pos]

                # Price regex (excludes unit prices)
                all_matches = list(
                    re.finditer(r"\b\d+[\u2009\s]*[\.,][\u2009\s]*\d{2}\b", window_text)
                )
                valid_prices = []
                for m in all_matches:
                    start_idx = m.start()
                    pre_context = window_text[
                        max(0, start_idx - 25) : start_idx
                    ].lower()
                    if any(
                        x in pre_context
                        for x in [
                            "kg =",
                            "kg=",
                            "liter =",
                            "liter=",
                            "l-preis",
                            "kg-preis",
                            "liter-preis",
                            "l =",
                            "l=",
                        ]
                    ):
                        continue
                    price_val = (
                        m.group(0)
                        .replace(" ", "")
                        .replace("\u2009", "")
                        .replace(",", ".")
                    )
                    valid_prices.append(price_val)

                price = "0.00"
                original_price = None
                if valid_prices:
                    price = valid_prices[0]
                    if len(valid_prices) > 1:
                        original_price = valid_prices[1]

                # Unit/size description
                desc_match = re.search(
                    r"\b\d+[- ]*(?:g|ml|kg|l|L|Fl\.)[- ]*(?:Packung|Becher|Beutel|Glas|Flasche|Stück|Schale)?\b",
                    window_text,
                    re.IGNORECASE,
                )
                desc = desc_match.group(0) if desc_match else ""

                picture_url = page_images.get(pidx, "")
                category = _infer_nord_category(p, window_text)

                discounts.append(
                    {
                        ATTR_DISCOUNT_TITLE: clean_name,
                        ATTR_DISCOUNT_PRICE: price,
                        ATTR_BASE_PRICE: f"{desc} (orig: {original_price})"
                        if original_price
                        else desc,
                        ATTR_PICTURE: picture_url,
                        ATTR_CATEGORY: category,
                    }
                )

        # Parse global validity dates
        valid_until_str = ""
        if len(page_texts) > 0:
            date_match = re.search(
                r"bis\s+S\s*a\s*\.\s*(\d+\.\d+\.?)", page_texts[0], re.IGNORECASE
            )
            if date_match:
                valid_until_str = date_match.group(1).replace(" ", "")

        return {
            "discounts": discounts,
            "valid_until": valid_until_str,
            "mag_url": mag_url,
        }
