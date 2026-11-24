"""Tests for ALDI Nord iPaper flyer parsing helpers."""

from __future__ import annotations

from custom_components.aldi.nord_parser import (
    extract_nord_brand,
    extract_nord_prices,
    infer_nord_category,
)


def test_extract_nord_prices_standard_and_superscript() -> None:
    """Test standard, reversed-superscript, and rotated split-badge prices."""
    assert extract_nord_prices("1-kg-Beutel 1. 99") == ("1.99", None)
    assert extract_nord_prices("900-g-Packung 29 ** 2. 49 * 3.") == ("2.29", "3.49")
    assert extract_nord_prices("Rahmspinat XXL 29 ** 1.") == ("1.29", None)
    assert extract_nord_prices("Fertiggericht XXL 6 9 . 9 *") == ("6.99", None)


def test_extract_nord_prices_skips_unit_prices() -> None:
    """Test unit prices inside parentheses or after unit labels are excluded."""
    text = (
        "Rahmspinat XXL 1-kg-Beutel (1 kg = 1.99) "
        "kg-Preis: 1.99 1. 49"
    )
    assert extract_nord_prices(text) == ("1.49", None)


def test_extract_nord_prices_fallback_zero() -> None:
    """Test missing price falls back cleanly to 0.00."""
    assert extract_nord_prices("Rahmspinat XXL 1-kg-Beutel ohne Preis") == ("0.00", None)


def test_extract_nord_brand_from_enrichment_and_prefix() -> None:
    """Test brand extraction from metadata and uppercase prefix while filtering noise."""
    assert extract_nord_brand({"brandName": "Iglo"}, "", "Rahmspinat XXL") == "Iglo"
    assert (
        extract_nord_brand({}, "TIEFKÜHLUNG! IGLO ", "Rahmspinat XXL") == "IGLO"
    )
    assert (
        extract_nord_brand({}, "AKTION NEU XXL ", "Fertiggericht") == ""
    )
    assert (
        extract_nord_brand({}, "DEUT SCHER LAN ", "Hackfleisch") == ""
    )


def test_infer_nord_category() -> None:
    """Test category inference from metadata and product keywords."""
    assert infer_nord_category({"category": "Tiefkühlkost"}, "") == "Tiefkühlkost"
    assert infer_nord_category({}, "Iglo Rahmspinat XXL") == "Tiefkühl"
    assert infer_nord_category({}, "Unbekannter Artikel") == "Angebote"
