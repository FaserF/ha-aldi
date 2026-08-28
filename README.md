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
| 🏷️ [**Grocery Deals (ha-grocery-deals)**](https://github.com/FaserF/ha-grocery-deals) | **Smart multi-store price comparison hub (aggregates all 5 integrations)** |
| 🔴 [**ha-rewe**](https://github.com/FaserF/ha-rewe) | REWE weekly offers, bonus points, coupons & product filters |
| 🟡 [**ha-edeka**](https://github.com/FaserF/ha-edeka) | EDEKA weekly offers, discounts & PAYBACK card |
| 🔵 [**ha-lidl**](https://github.com/FaserF/ha-lidl) | Lidl Plus weekly offers, coupons & digital receipts |
| 🔴 [**ha-norma**](https://github.com/FaserF/ha-norma) | Norma weekly store discounts & flyer offers |

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

> [!NOTE]
> For **Austria** and **Hungary**, the integration additionally fetches the full product list from the respective store's Nuxt-rendered web page (e.g. `hofer.at/angebote`), which contains structured price, brand, and product image data not present in the Publitas flipbook.

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

3. **Step 1 – Select your country**:
   - Choose one of the supported countries: Germany, Austria, Switzerland, Hungary, Italy, or Slovenia.
   - For Germany, you will additionally select a region: **ALDI SÜD**, **ALDI NORD**, or **Both**.
4. **Step 2** (Germany only) – Select region: **ALDI SÜD**, **ALDI NORD**, or **Both**.
5. Submit to create the device and entities.

---

## 🛠️ Options Flow

You can customise the poll interval of the integration at any time:

1. Go to **Settings > Devices & Services**.
2. Find **ALDI/Hofer Weekly Offers** and click **Configure**.
3. Set the **Update Interval** in hours (default is 24 hours, minimum is 1 hour).

## 🃏 Lovelace Cards

The community has built dedicated cards to display Aldi discounts beautifully in your dashboard.

### Custom Discounts Card
A dedicated Lovelace card maintained by the community:

[![Discounts Card](https://img.shields.io/badge/Lovelace-%20Discounts%20Card-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/schblondie/discounts-card)


---

## ❌ Unsupported Stores (ALDI US & Trader Joe's)

This integration **only supports European countries** (DE, AT, CH, HU, IT, SI). It does **not** support ALDI USA or Trader Joe's:

- **ALDI USA**: Circulars and weekly ads for ALDI US are hosted and powered by [Flipp](https://flipp.com) instead of ALDI's regional digital brochure backends. Flipp uses a proprietary API that relies on local ZIP codes and store-mapping infrastructure, which is incompatible with the direct leaflet API wrappers used in this integration.
- **Trader Joe's**: Although owned by ALDI Nord's owner family, Trader Joe's operates independently and has an "Everyday Low Prices" model. They **do not publish weekly sales or discounts** and do not offer coupons or weekly circular ads.

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
