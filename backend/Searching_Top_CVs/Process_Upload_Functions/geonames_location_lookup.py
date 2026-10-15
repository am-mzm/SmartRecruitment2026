"""SmartRecruitment GeoNames V2: indexed offline, read-only, conservative city lookup.

GeoNames geographic data: https://www.geonames.org/ (CC BY 4.0).
No remote calls. Uses indexed SQLite where available, otherwise source ZIPs
(for small regression fixtures and legacy setups). No database writes.
"""
from __future__ import annotations

import csv
import sqlite3
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile

DEFAULT_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "GeoReference"
COUNTRY_NAMES = {
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US",
    "ca": "CA", "can": "CA", "canada": "CA",
}


def _key(value):
    return " ".join(str(value or "").casefold().strip().split())


def _regions(directory: Path):
    by_key = {}
    mapping = directory / "canada_province_codes.txt"
    with mapping.open("r", encoding="utf-8-sig", newline="") as handle:
        lines = (line for line in handle if line.strip() and not line.lstrip().startswith(("#", "---")))
        for item in csv.DictReader(lines, delimiter="\t"):
            code = item["GeoNamesAdmin1Code"].strip().zfill(2)
            for alias in (item["ProvinceOrTerritory"], item["Abbreviation"], code):
                by_key[("CA", _key(alias))] = code
    admin_file = directory / "admin1CodesASCII.txt"
    with admin_file.open("r", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 2 or not row[0].startswith("US."):
                continue
            code = row[0].split(".", 1)[1]
            by_key[("US", _key(code))] = code
            by_key[("US", _key(row[1]))] = code
            if len(row) > 2:
                by_key[("US", _key(row[2]))] = code
    return by_key


def lookup_city(city: str, state: str = "", country: str = "", directory=DEFAULT_DIRECTORY):
    """Return a verified city center or None. Never silently guess ambiguous names.

    Country optional, but providing both country and state is strongly preferred.
    GeoNames populated-place results are selected by matching admin1 region and
    highest population within that region; city-only duplicates are rejected.
    """
    directory = Path(directory)
    target = _key(city)
    if not target or target in {"n/a", "unknown"}:
        return None
    country_code = COUNTRY_NAMES.get(_key(country)) if country else None
    if country and not country_code:
        return None
    codes = _regions(directory)
    available_countries = (country_code,) if country_code else ("US", "CA")
    matches = []
    index_path = directory / "geonames_cities.sqlite"
    if index_path.is_file():
        # URI mode=ro prevents creating or modifying the reference database.
        with closing(sqlite3.connect(index_path.as_uri() + "?mode=ro", uri=True)) as db:
            for iso in available_countries:
                state_code = codes.get((iso, _key(state))) if state else None
                if state and not state_code:
                    continue
                sql = ("SELECT city, country, state_code, latitude, longitude, "
                       "population, geoname_id FROM places WHERE city_key = ? AND country = ?")
                params = [target, iso]
                if state_code:
                    sql += " AND state_code = ?"
                    params.append(state_code)
                for row in db.execute(sql, params):
                    matches.append(dict(zip(("city", "country", "state_code", "latitude",
                                             "longitude", "population", "geoname_id"), row)))
    else:
        # Preserve the existing ZIP lookup for synthetic tests and unindexed data.
        for iso in available_countries:
            state_code = codes.get((iso, _key(state))) if state else None
            if state and not state_code:
                continue
            with ZipFile(directory / f"{iso}.zip") as archive:
                with archive.open(f"{iso}.txt") as data:
                    for raw in data:
                        fields = raw.decode("utf-8", errors="replace").rstrip("\r\n").split("\t")
                        if len(fields) != 19 or fields[6] != "P" or _key(fields[1]) != target:
                            continue
                        if state_code and fields[10] != state_code:
                            continue
                        try:
                            latitude, longitude = float(fields[4]), float(fields[5])
                            population = int(fields[14] or 0)
                        except ValueError:
                            continue
                        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                            continue
                        matches.append(dict(city=fields[1], country=iso, state_code=fields[10],
                                            latitude=latitude, longitude=longitude,
                                            population=population, geoname_id=fields[0]))
    if not matches and index_path.is_file():
        # Accent-insensitive fallback for names such as Montreal/Montr?al.
        # Only use it after exact matching fails; retain country/region checks.
        import unicodedata

        def without_accents(value):
            normalized = unicodedata.normalize("NFKD", value)
            return "".join(
                character for character in normalized
                if not unicodedata.combining(character)
            ).casefold()

        with closing(sqlite3.connect(index_path.as_uri() + "?mode=ro", uri=True)) as db:
            for iso in available_countries:
                state_code = codes.get((iso, _key(state))) if state else None
                if state and not state_code:
                    continue

                sql = (
                    "SELECT city, country, state_code, latitude, longitude, "
                    "population, geoname_id FROM places WHERE country = ?"
                )
                params = [iso]

                if state_code:
                    sql += " AND state_code = ?"
                    params.append(state_code)

                for row in db.execute(sql, params):
                    if without_accents(row[0]) != without_accents(target):
                        continue
                    matches.append(dict(zip(
                        ("city", "country", "state_code", "latitude",
                         "longitude", "population", "geoname_id"),
                        row
                    )))

    if not matches:
        return None
    # A single city may have multiple local GeoNames records. Prefer the main populated place.
    matches.sort(key=lambda row: row["population"], reverse=True)
    winner = matches[0]
    for other in matches[1:]:
        # Duplicate place names across different regions must be resolved by the caller.
        if (other["country"], other["state_code"]) != (winner["country"], winner["state_code"]):
            # Conservative exception for a clearly dominant city (e.g. Toronto vs an unpopulated hamlet).
            if winner["population"] < 10000 or winner["population"] < 10 * max(1, other["population"]):
                return None
    return {key: winner[key] for key in ("city", "country", "state_code", "latitude", "longitude", "geoname_id") } | {
        "geocode_source": "GeoNames", "geocode_precision": "CITY"
    }
