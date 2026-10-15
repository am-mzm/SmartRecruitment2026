"""Pure location search utilities. No network access, ChromaDB writes, or ranking changes.

Geocoding must be provided by a separate, validated provider/cache. Coordinates
represent an approximate postal area/city, not a candidate's travel willingness.
"""
from math import asin, cos, radians, sin, sqrt
from typing import Mapping, Optional

DEFAULT_RADIUS_MILES = 200.0
ENABLED_COUNTRIES = frozenset({'USA', 'Canada'})
COUNTRY_ALIASES = {'us': 'USA', 'usa': 'USA', 'united states': 'USA',
                   'can': 'Canada', 'ca': 'Canada', 'canada': 'Canada'}
REGION_ALIASES = {
    'on': 'ON', 'ontario': 'ON', 'ab': 'AB', 'alberta': 'AB',
    'bc': 'BC', 'british columbia': 'BC', 'qc': 'QC', 'quebec': 'QC',
    'mi': 'MI', 'michigan': 'MI', 'ny': 'NY', 'new york': 'NY',
    'ca': 'CA', 'california': 'CA', 'nj': 'NJ', 'new jersey': 'NJ',
}


def normalize_country(value: str) -> str:
    return COUNTRY_ALIASES.get(str(value or '').strip().casefold(), str(value or '').strip())


def normalize_region(value: str) -> str:
    val = str(value or '').strip()
    return REGION_ALIASES.get(val.casefold(), val.upper())


def haversine_miles(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    """Approximate great-circle miles, not road/rail commute distance."""
    a_lat, a_lon, b_lat, b_lon = map(float, (a_lat, a_lon, b_lat, b_lon))
    if not all((-90 <= x <= 90) for x in (a_lat, b_lat)):
        raise ValueError('Latitude out of range')
    if not all((-180 <= x <= 180) for x in (a_lon, b_lon)):
        raise ValueError('Longitude out of range')
    dl, dn = radians(b_lat - a_lat), radians(b_lon - a_lon)
    h = sin(dl/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dn/2)**2
    return 3958.7613 * 2 * asin(min(1.0, sqrt(max(0.0, h))))


def _coords(candidate: Mapping) -> Optional[tuple]:
    try:
        lat = candidate.get('candidate_latitude')
        lon = candidate.get('candidate_longitude')
        if lat is None or lon is None or str(lat).strip().upper() == 'N/A' or str(lon).strip().upper() == 'N/A':
            return None
        lat, lon = float(lat), float(lon)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return (lat, lon)
    except (TypeError, ValueError):
        return None


def location_match(candidate: Mapping, *, city: str = '', state: str = '',
                   country: str = '', center: Optional[tuple] = None,
                   radius_miles: float = DEFAULT_RADIUS_MILES) -> tuple[bool, Optional[float]]:
    """Return (eligible, distance). A city search requires a resolved center.

    Country/state filters are jurisdiction-wide. A city search uses a radius
    regardless of whether state/country were also supplied. Explicit country
    and region qualifiers still disambiguate the city center and candidate.
    """
    country = normalize_country(country)

    if country and country != 'Any' and country not in ENABLED_COUNTRIES:
        raise ValueError('Country is not enabled for location search')

    candidate_country = normalize_country(candidate.get('candidate_country'))

    if country == 'Any':
        if candidate_country not in ENABLED_COUNTRIES:
            return False, None
    elif country and candidate_country != country:
        return False, None
    # City search uses the resolved center and radius across region borders.
    # State/country values disambiguate the center, not candidate eligibility.
    if city:
        if radius_miles is None:
            candidate_city = str(candidate.get('candidate_city') or '').strip()
            if candidate_city.casefold() != city.strip().casefold():
                return False, None
            if state and normalize_region(candidate.get('candidate_state')) != normalize_region(state):
                return False, None
            return True, None
        if center is None:
            raise ValueError('City search requires a resolved, unambiguous center')
        if radius_miles <= 0:
            raise ValueError('Radius must be positive')
        coords = _coords(candidate)
        if coords is None:
            return False, None
        distance = haversine_miles(*center, *coords)
        return distance <= radius_miles, distance

    # Without a city, state/country are jurisdiction-wide filters.

    if state and normalize_region(candidate.get('candidate_state')) != normalize_region(state):
        return False, None
    return True, None


def sort_skills_first(candidates, *, score_key='relevance_score', distance_key='distance_miles'):
    """Preserve skills-first priority, using distance only for equal scores.

    Stable sort preserves original order if both score and distance tie.
    """
    def key(item):
        score = float(item[score_key])
        distance = item.get(distance_key)
        distance = float(distance) if distance is not None else float('inf')
        return (-score, distance)
    return sorted(candidates, key=key)


def filter_eligible_candidates(candidates, *, city='', state='', country='',
                               center=None, radius_miles=DEFAULT_RADIUS_MILES):
    """Filter candidate metadata without modifying scores or input order.

    Returns (eligible_candidates, distance_by_filename).
    City searches use straight-line distance across jurisdiction borders.
    """
    eligible = []
    distances = {}

    for candidate in candidates:
        matched, distance = location_match(
            candidate,
            city=city,
            state=state,
            country=country,
            center=center,
            radius_miles=radius_miles,
        )

        if not matched:
            continue

        eligible.append(candidate)

        filename = candidate.get('filename')
        if filename and distance is not None:
            distances[filename] = distance

    return eligible, distances
