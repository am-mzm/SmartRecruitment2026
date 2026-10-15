"""Build an offline GeoNames populated-place SQLite index (CC BY 4.0).

Run once on Windows; no ChromaDB/network access. Atomic replace on success.
GeoNames attribution: https://www.geonames.org/  https://creativecommons.org/licenses/by/4.0/
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from zipfile import ZipFile

REFERENCE = Path(__file__).resolve().parents[3] / "data" / "GeoReference"
OUTPUT = REFERENCE / "geonames_cities.sqlite"


def normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def build_index(directory: Path = REFERENCE) -> None:
    destination = directory / OUTPUT.name
    temporary = directory / (OUTPUT.name + ".building")
    for iso in ("US", "CA"):
        if not (directory / f"{iso}.zip").is_file():
            raise FileNotFoundError(directory / f"{iso}.zip")
    if temporary.exists():
        temporary.unlink()
    db = sqlite3.connect(temporary)
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("""CREATE TABLE places (
            geoname_id INTEGER PRIMARY KEY,
            city TEXT NOT NULL,
            city_key TEXT NOT NULL,
            country TEXT NOT NULL,
            state_code TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            population INTEGER NOT NULL
        )""")
        total = 0
        for iso in ("US", "CA"):
            batch = []
            count = 0
            with ZipFile(directory / f"{iso}.zip") as archive:
                with archive.open(f"{iso}.txt") as source:
                    for raw in source:
                        fields = raw.decode("utf-8", errors="replace").rstrip("\r\n").split("\t")
                        if len(fields) != 19 or fields[6] != "P" or not fields[1].strip():
                            continue
                        try:
                            lat, lon = float(fields[4]), float(fields[5])
                            population = int(fields[14] or 0)
                            geoname_id = int(fields[0])
                        except (ValueError, TypeError):
                            continue
                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            continue
                        batch.append((geoname_id, fields[1], normalize(fields[1]), iso,
                                      fields[10], lat, lon, population))
                        if len(batch) >= 10000:
                            db.executemany("INSERT OR REPLACE INTO places VALUES (?,?,?,?,?,?,?,?)", batch)
                            count += len(batch)
                            batch.clear()
                    if batch:
                        db.executemany("INSERT OR REPLACE INTO places VALUES (?,?,?,?,?,?,?,?)", batch)
                        count += len(batch)
            total += count
            print(f"{iso} populated-place rows: {count:,}", flush=True)
        db.execute("CREATE INDEX idx_place_name_country_region ON places(city_key, country, state_code)")
        db.execute("CREATE INDEX idx_place_country_region ON places(country, state_code)")
        db.commit()
        actual = db.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        assert integrity == "ok", f"SQLite integrity failed: {integrity}"
        assert actual > 1000 and total >= actual, f"Unexpected row count: {actual}"
        print(f"Total indexed cities/places: {actual:,}")
        print("SQLite integrity: PASS")
    except Exception:
        db.close()
        if temporary.exists():
            temporary.unlink()
        raise
    else:
        db.close()
        temporary.replace(destination)
        print(f"Index created: {destination}")
        print("CHROMADB: UNCHANGED")
        print("LINUX PRODUCTION: UNCHANGED")


if __name__ == "__main__":
    build_index()
