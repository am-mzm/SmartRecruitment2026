"""Conservative candidate contact-location extraction, without database dependencies.

Location extraction and search-country activation are separate configurations.
Country records may be added to COUNTRY_REGISTRY without changing the API.
Full candidate_address may contain personal information: restrict access and do
not expose it in ordinary candidate search results.
"""
import re
from typing import Dict

UNKNOWN = "N/A"

COUNTRY_REGISTRY = {
    "USA": {"aliases": ("USA", "US", "United States", "United States of America")},
    "Canada": {"aliases": ("Canada", "CAN", "CA")},
    "Pakistan": {"aliases": ("Pakistan",)},
    "India": {"aliases": ("India",)},
    "United Kingdom": {"aliases": ("United Kingdom", "UK")},
    "Nigeria": {"aliases": ("Nigeria",)},
}

# Only these countries are enabled for location-filtered SEARCH initially.
# Parsing recognizes all configured countries, whether searchable or not.
SEARCH_ENABLED_COUNTRIES = {"USA", "Canada"}

US_REGIONS = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
CA_REGIONS = set("AB BC MB NB NL NS NT NU ON PE QC SK YT".split())
US_REGION_NAMES = {
    "Michigan": "MI", "California": "CA", "New York": "NY", "Texas": "TX",
    "Florida": "FL", "Washington": "WA", "Illinois": "IL", "Ohio": "OH",
    "Georgia": "GA", "North Carolina": "NC", "Virginia": "VA",
}
CA_REGION_NAMES = {
    "Ontario": "ON", "Quebec": "QC", "Québec": "QC", "British Columbia": "BC",
    "Alberta": "AB", "Manitoba": "MB", "Nova Scotia": "NS",
    "New Brunswick": "NB", "Saskatchewan": "SK",
}

CITY = r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.' -]{1,55}?"
POSTAL_CA_PATTERN = r"[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d"
POSTAL_US_PATTERN = r"\d{5}(?:-\d{4})?"
STREET_SUFFIX = r"(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Boulevard|Blvd|Drive|Dr|Circle|Cir|Court|Ct|Crescent|Way|Place|Pl|Parkway|Pkwy)\.?"


def is_country_search_enabled(country: str) -> bool:
    """Search switch only; does not restrict extraction or ingestion."""
    return country in SEARCH_ENABLED_COUNTRIES


def _country_name(value: str) -> str:
    for canonical, settings in COUNTRY_REGISTRY.items():
        if value.casefold() in (alias.casefold() for alias in settings["aliases"]):
            return canonical
    return UNKNOWN


def _postal_suffix(value: str):
    """Return (location without postal, normalized postal) if a valid suffix exists."""
    m = re.search(rf"(?:\s+|,\s*)({POSTAL_CA_PATTERN}|{POSTAL_US_PATTERN})\s*$", value, re.I)
    if not m:
        return value.strip(), UNKNOWN
    postal = m.group(1).upper()
    if re.fullmatch(POSTAL_CA_PATTERN, postal, re.I):
        postal = re.sub(r"[ -]", "", postal)
        postal = postal[:3] + " " + postal[3:]
    return value[:m.start()].strip().rstrip(", "), postal


def _empty():
    return {
        "candidate_city": UNKNOWN,
        "candidate_state": UNKNOWN,
        "candidate_country": UNKNOWN,
        "candidate_postal_code": UNKNOWN,
        "candidate_location": UNKNOWN,
        "candidate_address": UNKNOWN,
        "remote_preference": UNKNOWN,
        "relocation_willingness": UNKNOWN,
    }


def _location_from_line(line: str):
    """Match strongly structured candidate header lines; do not infer residence."""
    line = re.sub(r"\s+", " ", line.strip()).strip(" |•")
    line = re.sub(r"^(?:location|based in|address)\s*:\s*", "", line, flags=re.I)
    line = re.split(r"\s+[|•]\s+", line, maxsplit=1)[0].strip()
    if not line:
        return None

    no_postal, postal = _postal_suffix(line)
    parts = [p.strip() for p in no_postal.split(",")]
    address = UNKNOWN
    if len(parts) >= 3 and re.match(rf"^\d+\s+.+\b{STREET_SUFFIX}$", parts[0], re.I):
        address = line  # Full address retained only as restricted candidate metadata.
        parts = parts[1:]

    city, state, country = UNKNOWN, UNKNOWN, UNKNOWN
    if len(parts) == 3:
        city, state, raw_country = parts
        country = _country_name(raw_country)
        # Allow country alias CA only as *explicit third token*.
        if country == UNKNOWN:
            return None
    elif len(parts) == 2:
        first, second = parts
        canonical = _country_name(first)
        if canonical != UNKNOWN and canonical == "Canada" and second.upper() in CA_REGIONS:
            # Canada, AB => no city specified
            country, state = canonical, second
        else:
            city, region = parts
            token = region.upper()
            if token in CA_REGIONS or region in CA_REGION_NAMES:
                country, state = "Canada", region
            elif token in US_REGIONS or region in US_REGION_NAMES:
                country, state = "USA", region
            else:
                country = _country_name(region)
                state = UNKNOWN
    elif len(parts) == 1:
        region = parts[0]
        # Known region-only notation, e.g. Greater Toronto Area.
        if region.casefold() == "greater toronto area":
            city, state, country = "Greater Toronto Area", "ON", "Canada"
        else:
            return None
    else:
        return None

    if country == UNKNOWN:
        return None
    if postal != UNKNOWN:
        if country == "Canada" and not re.fullmatch(POSTAL_CA_PATTERN, postal, re.I):
            return None
        if country == "USA" and not re.fullmatch(POSTAL_US_PATTERN, postal):
            return None

    # Exclude street addresses and postal codes from the general searchable location.
    location_parts = [p for p in (city, state, country) if p != UNKNOWN]
    return {
        "candidate_city": city or UNKNOWN,
        "candidate_state": state or UNKNOWN,
        "candidate_country": country,
        "candidate_postal_code": postal,
        "candidate_location": ", ".join(location_parts),
        "candidate_address": address,
    }



def _embedded_header_location(line: str):
    """Recognize location text inside a candidate contact line, not work history."""
    cleaned = re.sub(r"https?://\S+|www\.\S+|\S+@\S+\.\S+", " ", line, flags=re.I)
    cleaned = re.sub(r"(?i)location[-_ ]?arrow|location\s*:", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(?:phone|tel|email|e-mail|linkedin|github)\s*:", " | ", cleaned)
    cleaned = re.sub(r"(?<!\w)\+?\d[\d() ./-]{7,}\d", " | ", cleaned)
    cleaned = re.sub(r"[|•♂⌢]+", " | ", cleaned)
    # A city + state/province, optionally followed by a country or postal code.
    regions = sorted(US_REGIONS | CA_REGIONS | set(US_REGION_NAMES) | set(CA_REGION_NAMES),
                     key=len, reverse=True)
    region_pattern = "|".join(re.escape(x) for x in regions)
    city_pattern = r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.'-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.'-]*){0,3}"
    pattern = re.compile(
        rf"(?P<city>{city_pattern}),\s*(?P<region>{region_pattern})\b"
        rf"(?:\s+(?P<postal>{POSTAL_CA_PATTERN}|{POSTAL_US_PATTERN}))?"
        rf"(?:\s*,\s*(?P<country>Canada|CAN|CA|USA|US|United States))?\b",
        flags=re.I,
    )
    for m in pattern.finditer(cleaned):
        city = m.group("city").strip()
        # Remove labels and prefixed contact content while retaining multiword cities.
        city = re.split(r"\s+\|\s+|(?:^|\s)(?:location|address|based in)\s*:\s*",
                        city, flags=re.I)[-1].strip()
        if not city or city.casefold() in ("profile", "resume", "email", "phone"):
            continue
        country = m.group("country")
        raw = f"{city}, {m.group('region')}"
        if country:
            raw += f", {country}"
        if m.group("postal"):
            raw += f" {m.group('postal')}"
        parsed = _location_from_line(raw)
        if parsed:
            return parsed
    # Region-first Nigerian capital format.
    m = re.search(r"\bFCT\s*[-–]\s*Abuja\s*,\s*Nigeria\b", cleaned, re.I)
    if m:
        return _location_from_line("Abuja, FCT, Nigeria")
    return None


def _extended_street_location(line: str):
    """Canadian street, city, province, postal before country (no street in location)."""
    m = re.search(
        rf"(?P<street>\d+\s+[^,]{{3,100}}),\s*"
        rf"(?P<city>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .'’-]{{1,60}}),\s*"
        rf"(?P<region>Ontario|Alberta|Quebec|Québec|British Columbia|"
        rf"Manitoba|Nova Scotia|New Brunswick|Saskatchewan|ON|AB|QC|BC|MB|NS|NB|SK)"
        rf"\s+(?P<postal>{POSTAL_CA_PATTERN})\s*,\s*Canada\b",
        line, re.I,
    )
    if not m:
        return None
    parsed = _location_from_line(
        f"{m.group('city')}, {m.group('region')}, Canada {m.group('postal')}"
    )
    if parsed:
        parsed["candidate_address"] = m.group(0).rstrip(".")
    return parsed


def extract_candidate_location(text: str) -> Dict[str, str]:
    """Extract candidate header location and explicit work preferences only."""
    result = _empty()
    if not isinstance(text, str) or not text.strip():
        return result
    # Avoid assuming employer locations found later in work history are residence.
    header_lines = [x.strip() for x in text.splitlines()[:18] if x.strip()]
    header = "\n".join(header_lines)
    if re.search(r"\b(?:not willing to relocate|not open to relocation|cannot relocate)\b", header, re.I):
        result["relocation_willingness"] = "NO"
    elif re.search(r"\b(?:willing to relocate|open to relocation|willing to move|open to relocating)\b", header, re.I):
        result["relocation_willingness"] = "YES"
    if re.search(r"\b(?:not open to|not interested in|no)\s+remote\b", header, re.I):
        result["remote_preference"] = "NO"
    elif re.search(r"\b(?:open to|seeking|prefer(?:s|ring)?|available for)\s+(?:fully\s+|100%\s+)?remote\b|\bremote[- ]only\b", header, re.I):
        result["remote_preference"] = "YES"
    for line in header_lines:
        if re.search(r"(?i)^(?:work experience|employment history|work term|co-operative work terms|education|professional experience)\b", line):
            break
        parsed = (_extended_street_location(line)
                  or (_embedded_header_location(line) if re.search(r"(?i)\bFCT\s*[-–]\s*Abuja\s*,\s*Nigeria\b", line) else None)
                  or _location_from_line(line)
                  or _embedded_header_location(line))
        if parsed:
            result.update(parsed)
            break
    return result
