"""SmartRecruitment V1: safely attach GeoNames city coordinates to resume metadata.

Offline and read-only. Requires the existing candidate_location_extractor.py and
geonames_location_lookup.py in the same Python source directory.
GeoNames attribution: https://www.geonames.org/ (CC BY 4.0).
"""
from __future__ import annotations

from candidate_location_extractor import extract_candidate_location
from geonames_location_lookup import lookup_city

_COORD_FIELDS = ("candidate_latitude", "candidate_longitude", "geocode_source", "geocode_precision")
_UNKNOWN = {"", "n/a", "unknown", "none", "null"}
_SUPPORTED_GEOCODE_COUNTRIES = {"usa", "canada"}  # GeoNames index currently covers US and CA only


def enrich_candidate_location(metadata: dict, *, directory=None) -> dict:
    """Return a new metadata dictionary; never alter the original or write to DB.

    Existing coordinate fields are cleared if the location fails resolution.
    No address or postal code is used for geocoding (CITY precision only).
    """
    enriched = dict(metadata)
    for field in _COORD_FIELDS:
        enriched.pop(field, None)
    city = str(enriched.get("candidate_city") or "").strip()
    state = str(enriched.get("candidate_state") or "").strip()
    country = str(enriched.get("candidate_country") or "").strip()
    if city.casefold() in _UNKNOWN or country.casefold() in _UNKNOWN:
        return enriched
    if country.casefold() not in _SUPPORTED_GEOCODE_COUNTRIES:
        return enriched
    options = {} if directory is None else {"directory": directory}
    try:
        resolved = lookup_city(city, state if state.casefold() not in _UNKNOWN else "", country, **options)
    except (FileNotFoundError, OSError, ValueError):
        return enriched
    if resolved is None:
        return enriched
    enriched.update({
        "candidate_latitude": float(resolved["latitude"]),
        "candidate_longitude": float(resolved["longitude"]),
        "geocode_source": resolved["geocode_source"],
        "geocode_precision": resolved["geocode_precision"],
    })
    return enriched


def extract_and_enrich_candidate_location(resume_text: str, *, directory=None) -> dict:
    """Use the existing conservative extractor, then geocode supported locations."""
    return enrich_candidate_location(extract_candidate_location(resume_text), directory=directory)
