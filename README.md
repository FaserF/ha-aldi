<div align="center">
  <h1>ALDI/Hofer Weekly Offers (for Home Assistant) 🛒</h1>
  <p><strong>A secure, robust Home Assistant integration that fetches weekly offers, discounts, and upcoming flyers from ALDI & HOFER directly from official digital brochure APIs.</strong></p>

  [![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz)
  [![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-aldi/latest/aldi.zip?label=Downloads%20(Current%20release)&style=for-the-badge)](https://github.com/FaserF/ha-aldi/releases)
  [![GitHub Release](https://img.shields.io/github/v/release/FaserF/ha-aldi?style=for-the-badge)](https://github.com/FaserF/ha-aldi/releases)
  [![License](https://img.shields.io/github/license/FaserF/ha-aldi?style=for-the-badge)](LICENSE)
</div>

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [✨ Features](#-features) | [🌍 Supported Countries](#-supported-countries) | [📦 Installation](#-installation) | [⚙️ Configuration](#-configuration) |
| [🛠️ Options](#-options-flow) | [❌ Unsupported Stores](#-unsupported-stores-aldi-us--trader-joes) | [🧑‍💻 Development](#-development) | [📄 License](#-license) |

### Why use this integration?
Instead of brittle web scraping, this integration uses ALDI's and HOFER's official leaflet backend structures (Publitas for ALDI SÜD, iPaper/Next.js-API for ALDI NORD, AEM/Nuxt for international countries) to fetch high-fidelity weekly offers as structured data.

---

### 🛒 Supermarket Family & Deals Hub

Check out our full collection of Home Assistant supermarket integrations and the multi-store aggregator:

| Repository | Description |
| :--- | :--- |
| 🏷️ [**Grocery Deals (ha-grocery-deals)**](https://github.com/FaserF/ha-grocery-deals) | **Smart multi-store price comparison hub (aggregates all integrations)** |
| 🔴 [**ha-rewe**](https://github.com/FaserF/ha-rewe) | REWE weekly offers, bonus points, coupons & product filters |
| 🟡 [**ha-edeka**](https://github.com/FaserF/ha-edeka) | EDEKA weekly offers, discounts & PAYBACK card |
| 🔵 [**ha-lidl**](https://github.com/FaserF/ha-lidl) | Lidl Plus weekly offers, coupons & digital receipts |
| 🔴 [**ha-norma**](https://github.com/FaserF/ha-norma) | Norma weekly store discounts & flyer offers |
| 🔴 [**ha-penny**](https://github.com/FaserF/ha-penny) | Penny weekly store discounts, coupons & flyer offers |

---

It groups all sensors under a single branded device entity per country, and implements advanced security rules (locks, random jitters, failure backoff) to prevent blocking and keep your connection secure.

---

## ✨ Features

- **🛒 Multi-Week Offers Tracking**:
  - **Offers**: Current week's discounted items count, with attributes containing titles, prices, descriptions, image links, and categories.
  - **Offers Next**: Next week's upcoming deals.
  - **Offers Preview**: Preview week's upcoming deals (2 weeks in advance).

> [!NOTE]
> **Offers Next** and **Offers Preview** count may be `0` or contain very few items (like recipes) during the week. This is because ALDI only publishes/populates the interactive product hotspots on their servers a few days before the respective brochure goes live.

- **🌍 Multi-Country Support**: Supports ALDI and HOFER stores across 6 European countries (see [Supported Countries](#-supported-countries)).
- **🛡️ Rate-Limiting & Anti-Ban Protections**:
  - **First-Fetch Optimisation**: Skips jitter sleep on initial setup so the first refresh completes instantly.
  - **Lock Queueing**: A domain-wide lock ensures concurrent updates run sequentially.
  - **Random Jitter**: Introduces a 5–15 second delay between requests.
  - **Restart-Resistance**: Saves parsed data to HA storage cache to survive reboots without hitting the API.
  - **Dynamic Backoff**: Backs off for up to 24 hours on 403 or 429 errors, and minutes on network failures.
- **⚙️ Device-Based Grouping**:
  - All sensors and buttons are grouped under a main branded ALDI/Hofer device.
  - **Visit Flyer Button**: The device registry provides a dynamic configuration URL that takes you straight to your specific week's online brochure page.
- **🎛️ Manual Force Update**:
  - A **Force Update** button entity allows manually triggering an API update on demand (disabled by default to avoid accidental triggers).
- **🔍 Diagnostic Downloads**:
  - Full support for Home Assistant UI Diagnostics. Download complete configurations with identifiers and session details automatically redacted.

---

## 🌍 Supported Countries

| Country | Brand | Data Source |
| :--- | :--- | :--- |
| 🇩🇪 Germany (ALDI SÜD) | ALDI SÜD | Publitas flipbook API |
| 🇩🇪 Germany (ALDI NORD) | ALDI NORD | iPaper / Next.js API |
| 🇦🇹 Austria | HOFER | Publitas + Nuxt SSR API |
| 🇨🇭 Switzerland | ALDI Suisse | Publitas flipbook API |
| 🇭🇺 Hungary | ALDI Hungary | Publitas + Nuxt SSR API |
| 🇮🇹 Italy | ALDI Italy | Publitas flipbook API |
| 🇸🇮 Slovenia | HOFER Slovenia | Publitas flipbook API |
| 🇺🇸 United States | ALDI US | Instacart Storefront Pro SSR (ZIP code based) |

> [!NOTE]
> For **Austria** and **Hungary**, the integration additionally fetches the full product list from the respective store's Nuxt-rendered web page (e.g. `hofer.at/angebote`), which contains structured price, brand, and product image data not present in the Publitas flipbook.
>
> For the **United States**, the weekly specials and circulars are provided via ALDI US's Instacart Storefront architecture. You will be asked for your 5-digit ZIP code during configuration to load the correct local weekly ad.

---

## ❤️ Support This Project

> I maintain this integration in my **free time alongside my regular job**.
>
> **This project is and will always remain 100% free.**
>
> Donations are completely voluntary — but they help me stay motivated and dedicate more time to maintaining open-source tools!

<div align="center">

[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/FaserF)

</div>

---

## 🔌 Recommended Hardware & Ecosystem Links

| Device / Service | Integration Use Case | Link |
| :--- | :--- | :--- |
| **Home Assistant Green & Offizielle Smart-Home-Hardware** | Empfohlene Hardware-Basis für lokale Home Assistant Integrationen | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-hardware) |
| **Home Assistant Connect ZBT-1 (Zigbee / Thread)** | Lokales Zigbee2MQTT, ZHA & Matter-over-Thread Funknetz | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-zigbee) |


---

## 📦 Installation

### HACS (Recommended)

This integration is fully compatible with [HACS](https://hacs.xyz/).

1. Open HACS in Home Assistant.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add `FaserF/ha-aldi` with category **Integration**.
4. Search for **"ALDI/Hofer Weekly Offers"**.
5. Install and restart Home Assistant.

[![Open HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-aldi&category=integration)

### Manual Installation

1. Download the latest release zip file.
2. Extract the `custom_components/aldi` folder into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. Navigate to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **ALDI/Hofer Weekly Offers**.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aldi)

3. **Step 1 – Select your country / region**:
   - Choose one of the supported countries: Germany, Austria, Switzerland, Hungary, Italy, Slovenia, or United States.
4. **Step 2**:
   - **Germany**: Select region (**ALDI SÜD**, **ALDI NORD**, or **Both**).
   - **United States**: Enter your 5-digit **ZIP Code** (e.g. `60174`).
   - **Other European Countries**: Automatically configured for the national catalog.
5. Submit to create the device and entities.

---

## 🛠️ Options Flow

You can customise integration settings at any time:

1. Go to **Settings > Devices & Services**.
2. Find **ALDI/Hofer Weekly Offers** and click **Configure**.
3. Configure the available options:
   - **Update Interval**: Set the update interval in hours (default is 24 hours, minimum is 1 hour).
   - **Product Filters**: Add keywords to monitor specific products (e.g. `Kaffee`, `Butter`, `Milch`, `Brot`).

### 🔍 Product Filter Sensors
When product filter keywords are configured in the Options Flow, the integration automatically creates dedicated filter sensor entities (`sensor.aldi_<region>_filter_<keyword>`):
- **State**: Displays the best offer price found or `Nicht im Angebot` if no match exists.
- **Attributes**: Includes `on_sale` (boolean), `match_count`, `best_price`, `base_price`, `product_title`, `category`, `valid_until`, `picture_link`, and the list of all matching items (`matches`).
- **Dynamic Cleanup**: Removing a keyword from the options automatically cleans up its sensor entity from the entity registry.

## 🃏 Lovelace Cards

The community has built dedicated cards to display Aldi discounts beautifully in your dashboard.

### Custom Discounts Card
A dedicated Lovelace card maintained by the community:

[![Discounts Card](https://img.shields.io/badge/Lovelace-%20Discounts%20Card-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/schblondie/discounts-card)


---

## ℹ️ Technical Differences & Maintenance Scope

> [!IMPORTANT]
> **Primary Maintainer Scope**: The core focus and primary maintenance of this repository is for **ALDI EU (Germany, Austria, Switzerland, Hungary, Italy, Slovenia)**. Support for ALDI US is provided on a best-effort basis for the international community.

### Technical Architecture Comparison:
- **ALDI EU (DE, AT, CH, HU, IT, SI)**: European ALDI & HOFER entities rely on Publitas digital flipbook APIs, Next.js embedded data, and Adobe Experience Manager (AEM) EMEA endpoints (`publish.prod.emea.cms.aldi.cx`). Offers are organized weekly by calendar week (`KW`).
- **ALDI US**: ALDI US operates on an Instacart Storefront Pro infrastructure. Offers are location- and ZIP-dependent, extracted from server-side rendered state (`DocumentCache`).

### Unsupported: Trader Joe's
Although owned by ALDI Nord's owner family, **Trader Joe's** operates independently and uses an "Everyday Low Prices" model. They **do not publish weekly sales or discounts** and do not offer coupons or circular ads.

---

## 🧑‍💻 Development

### Ruff Linter
Ensure formatting and import order matches:
```bash
ruff check . --fix
ruff format .
```

### Type Checking
Ensure all files pass strict type checking:
```bash
mypy .
```

### Testing
To run the automated test suite:
```bash
pytest
```

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
