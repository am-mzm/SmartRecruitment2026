"""Regression suite uses tiny synthetic GeoNames files; no production datasets needed."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from geonames_location_lookup import lookup_city


def make_row(name, iso, region, latitude, longitude, population, feature="P"):
    row = [""] * 19
    row[0],row[1],row[4],row[5],row[6],row[8],row[10],row[14] = (
        "123",name,str(latitude),str(longitude),feature,iso,region,str(population))
    return "\t".join(row) + "\n"


class GeoNamesLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / "canada_province_codes.txt").write_text(
            "CountryISO\tProvinceOrTerritory\tAbbreviation\tGeoNamesAdmin1Code\n"
            "CA\tOntario\tON\t08\nCA\tBritish Columbia\tBC\t02\n", encoding="utf-8")
        (self.base / "admin1CodesASCII.txt").write_text(
            "US.MI\tMichigan\tMichigan\t5001836\n"
            "US.NY\tNew York\tNew York\t5128638\n",encoding="utf-8")
        us = (make_row("Ann Arbor","US","MI",42.28,-83.74,117070)
              + make_row("Troy","US","MI",42.60,-83.15,83280)
              + make_row("Troy","US","NY",42.73,-73.69,49906)
              + make_row("Toronto","US","NY",43.0,-77.0,0)
              + make_row("Ann Arbor","US","MI",42.29,-83.75,0,"H"))
        ca = (make_row("Toronto","CA","08",43.70,-79.40,2794356)
              + make_row("Toronto","CA","09",46.4,-63.3,0)
              + make_row("Mississauga","CA","08",43.58,-79.66,717961)
              + make_row("Hamilton","CA","08",43.25,-79.85,569353))
        for iso,content in (("US",us),("CA",ca)):
            with ZipFile(self.base / f"{iso}.zip", "w", ZIP_DEFLATED) as z:
                z.writestr(f"{iso}.txt",content)

    def tearDown(self):
        self.temp.cleanup()

    def get(self,city,state="",country=""):
        return lookup_city(city,state,country,self.base)

    def create_index(self):
        db = sqlite3.connect(self.base / "geonames_cities.sqlite")
        db.execute("""CREATE TABLE places (
            geoname_id INTEGER PRIMARY KEY, city TEXT NOT NULL, city_key TEXT NOT NULL,
            country TEXT NOT NULL, state_code TEXT NOT NULL, latitude REAL NOT NULL,
            longitude REAL NOT NULL, population INTEGER NOT NULL)""")
        db.executemany("INSERT INTO places VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (1, "Ann Arbor", "ann arbor", "US", "MI", 42.28, -83.74, 117070),
            (2, "Toronto", "toronto", "CA", "08", 43.70, -79.40, 2794356),
            (3, "Troy", "troy", "US", "MI", 42.60, -83.15, 83280),
            (4, "Troy", "troy", "US", "NY", 42.73, -73.69, 49906),
            (5, "Toronto", "toronto", "CA", "09", 46.4, -63.3, 0),
        ])
        db.commit()
        db.close()

    def test_sqlite_lookup_without_zip_files(self):
        self.create_index()
        for iso in ("US", "CA"):
            (self.base / f"{iso}.zip").unlink()
        result = self.get("Ann Arbor", "Michigan", "USA")
        self.assertEqual(result["geoname_id"], 1)
        self.assertEqual(result["latitude"], 42.28)
        self.assertEqual(result["geocode_source"], "GeoNames")

    def test_sqlite_ambiguity_and_dominance(self):
        self.create_index()
        self.assertIsNone(self.get("Troy"))
        self.assertEqual(self.get("Troy", "MI", "US")["state_code"], "MI")
        self.assertEqual(self.get("Toronto")["country"], "CA")

    def test_city_state_country(self):
        self.assertEqual(self.get("Ann Arbor","MI","USA")["country"],"US")
    def test_full_state(self):
        self.assertEqual(self.get("Ann Arbor","Michigan","US")["state_code"],"MI")
    def test_canada_full_province(self):
        self.assertEqual(self.get("Toronto","Ontario","Canada")["state_code"],"08")
    def test_canada_abbreviation(self):
        self.assertEqual(self.get("Toronto","ON","CA")["country"],"CA")
    def test_canada_numeric_code(self):
        self.assertEqual(self.get("Toronto","08","Canada")["state_code"],"08")
    def test_toronto_dominant_city(self):
        self.assertEqual(self.get("Toronto")["country"],"CA")
    def test_ambiguous_troy_without_region(self):
        self.assertIsNone(self.get("Troy"))
    def test_troy_with_region(self):
        self.assertEqual(self.get("Troy","MI","USA")["state_code"],"MI")
    def test_unknown_city(self):
        self.assertIsNone(self.get("Imaginaryville","MI","US"))
    def test_invalid_state(self):
        self.assertIsNone(self.get("Toronto","XX","Canada"))
    def test_unsupported_country(self):
        self.assertIsNone(self.get("Karachi","Sindh","Pakistan"))
    def test_missing_city(self):
        self.assertIsNone(self.get("N/A"))
    def test_coordinates_and_attribution(self):
        r=self.get("Mississauga","ON","Canada")
        self.assertEqual((r["latitude"],r["longitude"]),(43.58,-79.66))
        self.assertEqual(r["geocode_source"],"GeoNames")
        self.assertEqual(r["geocode_precision"],"CITY")

if __name__ == "__main__":
    unittest.main()
