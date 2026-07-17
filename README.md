<div align="center">
  <h1>ALDI Weekly Offers (for Home Assistant) 🛒</h1>
  <p><strong>A secure, robust Home Assistant integration that fetches weekly offers, discounts, and upcoming flyers from ALDI SÜD & ALDI NORD directly from official digital brochure APIs.</strong></p>

  [![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz)
  [![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-aldi/latest/aldi.zip?label=Downloads%20(Current%20release)&style=for-the-badge)](https://github.com/FaserF/ha-aldi/releases)
  [![GitHub Release](https://img.shields.io/github/v/release/FaserF/ha-aldi?style=for-the-badge)](https://github.com/FaserF/ha-aldi/releases)
  [![License](https://img.shields.io/github/license/FaserF/ha-aldi?style=for-the-badge)](LICENSE)
</div>

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [✨ Features](#-features) | [📦 Installation](#-installation) | [⚙️ Configuration](#-configuration) | [🛠️ Options](#-options-flow) |
| [🧑‍💻 Development](#-development) | [📄 License](#-license) | | |

### Why use this integration?
Instead of brittle web scraping, this integration uses ALDI's official leaflet backend structures (Publitas for SÜD, iPaper/NextJS-API for NORD) to fetch high-fidelity weekly offers as structured data.

It groups all sensors under a single ALDI SÜD or ALDI NORD device entity, and implements advanced security rules (locks, random jitters, failures backoff) to prevent blockings and keep your connection secure.

---

## ✨ Features

- **🛒 Multi-Week Offers Tracking**:
  - **Offers**: Current week's discounted items count, with attributes containing titles, prices, descriptions, image links, and categories.
  - **Offers Next**: Next week's upcoming deals.
  - **Offers Preview**: Preview week's upcoming deals (2 weeks in advance).

> [!NOTE]
> **Offers Next** and **Offers Preview** count may be `0` or contain very few items (like recipes) during the week. This is because ALDI only publishes/populates the interactive product hotspots on their servers a few days before the respective brochure goes live.

- **🛡️ Rate-Limiting & Anti-Ban Protections**:
  - **First-Fetch Optimisation**: Skips jitter sleep on initial setup so the first refresh completes instantly.
  - **Lock Queueing**: A domain-wide lock ensures concurrent updates run sequentially.
  - **Random Jitter**: Introduces a 5–15 second delay between requests.
  - **Restart-Resistance**: Saves parsed data to HA storage cache to survive reboots without hitting the API.
  - **Dynamic Backoff**: Backs off for up to 24 hours on 403 or 429 errors, and minutes on network failures.
- **⚙️ Device-Based Grouping**:
  - All sensors and buttons are grouped under a main regional ALDI device.
  - **Visit Flyer Button**: The device registry provides a dynamic configuration URL that takes you straight to your specific week's online brochure page.
- **🎛️ Manual Force Update**:
  - A **Force Update** button entity allows manually triggering an API update on demand (disabled by default to avoid accidental triggers).
- **🔍 Diagnostic Downloads**:
  - Full support for Home Assistant UI Diagnostics. Download complete configurations with identifiers and session details automatically redacted.

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
4. Search for "ALDI Weekly Offers".
5. Install and restart Home Assistant.

[![Open HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-aldi&category=integration)

### Manual Installation

1. Download the latest release zip file.
2. Extract the `custom_components/aldi` folder into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. Navigate to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **ALDI Weekly Offers**.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aldi)
3. Select your region of interest: **ALDI SÜD**, **ALDI NORD**, or **Both**.
4. Submit to create the device and entities.

---

## 🛠️ Options Flow

You can customise the poll interval of the integration at any time:

1. Go to **Settings > Devices & Services**.
2. Find **ALDI Weekly Offers** and click **Configure**.
3. Set the **Update Interval** in hours (default is 24 hours, minimum is 1 hour).

---

## 🧑‍💻 Development

### Ruff Linter
Ensure formatting and import order matches:
```bash
ruff check . --fix
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

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
