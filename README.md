# ALDI Weekly Offers for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-aldi.svg?style=flat-square)](https://github.com/FaserF/ha-aldi/releases)
[![License](https://img.shields.io/github/license/FaserF/ha-aldi.svg?style=flat-square)](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)

Exposes current and upcoming weekly offers from **ALDI Süd** and **ALDI Nord** directly inside Home Assistant.

## Features

- **Aldi Süd & Nord Support**: Track one or both regions. Configured easily during the setup flow.
- **Current & Upcoming Offers**: Offers are split into separate sensors for current week and next week preview.
- **Robust Anti-Ban System**: Mimics real browser requests using randomized user agents, headers, connection limits, and automatic back-offs in case of rate limits or access restrictions.
- **Rich State Attributes**: Every sensor has a listing of product titles, prices, original/previous prices, pictures (flyer page images for ALDI Nord / direct product images for ALDI Süd), categories, and validity dates.

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant.
2. Click on **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Add the URL of this repository: `https://github.com/FaserF/ha-aldi` with the category `Integration`.
5. Click **Add** and install the **ALDI Weekly Offers** integration.
6. Restart Home Assistant.

### Manual Installation

1. Download the latest release.
2. Copy the `custom_components/aldi` directory into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **ALDI Weekly Offers**.
3. Choose the region you want to track (ALDI SÜD, ALDI NORD, or both).
4. Save the configuration.

You can configure the update interval (default is 12 hours) in the integration options.

## Sponsors

If you like this integration, consider supporting development!
