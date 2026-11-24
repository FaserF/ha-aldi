"""ALDI Nord iPaper flyer parsing helpers."""

from __future__ import annotations

import re
from typing import Any

# Flyer badges, Haltungsform seal OCR fragments, and unit/promo words that are not brands
_NON_BRAND_PHRASES: tuple[str, ...] = (
    "AKTION",
    "NEU",
    "XXL",
    "UVP",
    "SPAREN",
    "BIS ZU",
    "IM AUFSTELLER",
    "ZUM ALDI PREIS",
    "GUTES FÜR ALLE",
    "FRISCHE FÜR ALLE",
    "BIO FÜR ALLE",
    "AUS DER TIEFKÜHLUNG",
    "AUS DER KÜHLUNG",
    "KI GENERIERT",
    "BACKWAREN ZUM GENIESSEN",
    "UNVERPACKT",
    "PREIS",
    "STÜCK",
    "PACKUNG",
    "BEUTEL",
    "SCHALE",
    "DOSE",
    "GLAS",
    "FLASCHE",
    "KRACHER",
    "WOCHENEND",
    "SUPER",
    "KNALLER",
    "TIPP",
    "RABATT",
    "SERVIERVORSCHLAG",
)

_SEAL_NOISE_TOKENS: frozenset[str] = frozenset(
    {
        "AUS",
        "DEUT",
        "AFT",
        "GUTES",
        "SCHER",
        "LAN",
        "DWIRTSCH",
        "FROREN",
        "TIEFGEFROREN",
        "WEIDE",
        "STALL",
        "BIO",
        "PRO",
        "OD",
        "KI",
        "ATG",
        "HKL",
        "UVP",
    }
)

_STD_PRICE_RE = re.compile(r"\b(\d{1,4})[\u2009\s]*([\.,])[\u2009\s]*(\d{2})\b")
_REV_PRICE_RE = re.compile(r"(?<!\d)(\d{2})[\u2009\s]*\*{1,3}[\u2009\s]*(\d{1,3})\.")
_SPLIT_BADGE_PRICE_RE = re.compile(r"\b(\d)\s+(\d)\s*\.\s*(\d)\s*\*")

_UNIT_ASSIGN_RE = re.compile(
    r"(?:kg|liter|l|anwendung(?:en)?|waschladung(?:en)?|st[üu]ck|blatt|preis)"
    r"(?:-preis)?\s*[=:]\s*(?:[\d.,]+\s*/\s*)?$",
    re.IGNORECASE,
)
_UNIT_LABEL_RE = re.compile(
    r"(?:kg|liter|l|100\s*-?\s*g|\d+\s*-?\s*ml)-preis\s*[:=]?\s*$",
    re.IGNORECASE,
)

_KEYWORD_CATEGORIES: list[tuple[str, str]] = [
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
        r"tiefk[üu]hl|tk-|tiefgek[üu]hlt|pizza|eis(becher|würfel|creme)?|rahmspinat",
        "Tiefkühl",
    ),
    (
        r"getr[äa]nk|wasser|saft|limo|cola|bier|wein|sekt|kaffee|tee|kakao",
        "Getränke",
    ),
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


def make_lenient_regex(name: str) -> str:
    """Build a whitespace/soft-hyphen tolerant regex for matching product names."""
    clean = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß]", "", name)
    if not clean:
        return ""
    return "".join(re.escape(char) + r"[\s\u00ad\u2009-]*" for char in clean)


def extract_nord_prices(window_text: str) -> tuple[str, str | None]:
    """Extract current offer price and optional original price from an ALDI Nord text window.

    Handles standard prices ('1. 99', '2,49'), split superscript cents-first badges
    ('29 ** 1.' -> '1.29', '49 ** 3.' -> '3.49'), and rotated split badges ('6 9 . 9 *' -> '6.99'),
    while accurately excluding unit prices inside parentheses or right after unit labels.
    """
    candidates: list[tuple[int, int, str]] = []
    for m in _STD_PRICE_RE.finditer(window_text):
        candidates.append((m.start(), m.end(), f"{int(m.group(1))}.{m.group(3)}"))
    for m in _REV_PRICE_RE.finditer(window_text):
        candidates.append((m.start(), m.end(), f"{int(m.group(2))}.{m.group(1)}"))
    for m in _SPLIT_BADGE_PRICE_RE.finditer(window_text):
        d1, d2, d3 = m.group(1), m.group(2), m.group(3)
        if d2 == d3:
            candidates.append((m.start(), m.end(), f"{int(d1)}.{d2}{d3}"))

    candidates.sort(key=lambda c: (c[0], -(c[1] - c[0])))
    deduped: list[tuple[int, int, str]] = []
    last_end = -1
    for start, end, val in candidates:
        if start < last_end:
            continue
        deduped.append((start, end, val))
        last_end = end

    valid_prices: list[tuple[int, str]] = []
    for start, _end, val in deduped:
        pre = window_text[max(0, start - 50) : start].lower()
        last_open = pre.rfind("(")
        last_close = pre.rfind(")")
        if last_open > last_close:
            inside = pre[last_open:]
            if any(
                k in inside
                for k in (
                    "=",
                    "preis",
                    "kg",
                    "liter",
                    "anwendung",
                    "waschladung",
                    "stück",
                    "blatt",
                )
            ):
                continue

        immediate = pre[-25:]
        if _UNIT_ASSIGN_RE.search(immediate) or _UNIT_LABEL_RE.search(immediate):
            continue

        valid_prices.append((start, val))

    if not valid_prices:
        return "0.00", None

    first_pos, first_price = valid_prices[0]
    original_price: str | None = None
    if len(valid_prices) > 1:
        second_pos, second_price = valid_prices[1]
        try:
            if (second_pos - first_pos) <= 30 and float(second_price) > float(
                first_price
            ):
                original_price = second_price
        except ValueError:
            pass

    return first_price, original_price


def extract_nord_brand(
    enrichment: dict[str, Any], pre_text: str, clean_name: str
) -> str:
    """Extract brand name from enrichment metadata or uppercase prefix in pageTexts."""
    for field in ("brand", "brandName", "manufacturer"):
        val = enrichment.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    tail = pre_text[-80:].replace("\u2009", " ").strip()
    if not tail:
        return ""

    # Only examine the trailing clause after sentence/badge punctuation
    tail = re.split(r"[!?;,)\.*%]", tail)[-1].strip()
    if not tail:
        return ""

    tokens = re.findall(r"[A-Za-zÄÖÜäöüß0-9'’&\-]+", tail)
    brand_tokens: list[str] = []
    for tok in reversed(tokens):
        if re.fullmatch(r"\d+(?:[.,]\d+)?", tok):
            break
        if tok in {"g", "kg", "ml", "l", "L"}:
            break
        if re.search(r"[A-ZÄÖÜ]", tok) and not re.search(r"[a-zäöüß]", tok):
            brand_tokens.append(tok)
        else:
            break

    if not brand_tokens:
        return ""

    brand_tokens.reverse()
    candidate = " ".join(brand_tokens).strip(" -&")

    changed = True
    while changed and candidate:
        changed = False
        for phrase in sorted(_NON_BRAND_PHRASES, key=len, reverse=True):
            if candidate == phrase:
                candidate = ""
                changed = True
                break
            if candidate.startswith(phrase + " "):
                candidate = candidate[len(phrase) :].strip()
                changed = True
                break
            if candidate.endswith(" " + phrase):
                candidate = candidate[: -len(phrase)].strip()
                changed = True
                break

    if not candidate or len(candidate) < 2:
        return ""
    cand_tokens = candidate.split()
    if any(t in _SEAL_NOISE_TOKENS for t in cand_tokens):
        return ""
    if len(cand_tokens[0]) == 1 and cand_tokens[0].isalpha():
        return ""
    if candidate.lower() in clean_name.lower():
        return ""
    return candidate


def infer_nord_category(enrichment: dict[str, Any], window: str) -> str:
    """Return a category string for an ALDI NORD enrichment item."""
    for field in ("category", "productType", "productCategory", "type_label"):
        val = enrichment.get(field)
        if (
            val
            and isinstance(val, str)
            and val not in {"product", "13", "Automatic", "Manual"}
        ):
            return val.strip()

    w_lower = window.lower()
    for pattern, label in _KEYWORD_CATEGORIES:
        if re.search(pattern, w_lower):
            return label

    return "Angebote"
