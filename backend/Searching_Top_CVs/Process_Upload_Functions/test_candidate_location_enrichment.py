import unittest
from unittest.mock import patch

from candidate_location_enrichment import enrich_candidate_location, extract_and_enrich_candidate_location

RESOLVED = {"latitude": 43.70643, "longitude": -79.39864, "geocode_source": "GeoNames", "geocode_precision": "CITY"}

class CandidateLocationEnrichmentTests(unittest.TestCase):
    @patch("candidate_location_enrichment.lookup_city", return_value=RESOLVED)
    def test_canada(self, lookup):
        original = {"candidate_city": "Toronto", "candidate_state": "ON", "candidate_country": "Canada", "candidate_postal_code": "M5V 1A1"}
        result = enrich_candidate_location(original)
        self.assertEqual(result["candidate_latitude"], 43.70643)
        self.assertEqual(result["candidate_postal_code"], "M5V 1A1")
        self.assertNotIn("candidate_latitude", original)
        lookup.assert_called_once_with("Toronto", "ON", "Canada")

    @patch("candidate_location_enrichment.lookup_city", return_value=None)
    def test_ambiguous_city_unresolved(self, lookup):
        result = enrich_candidate_location({"candidate_city": "Troy", "candidate_state": "N/A", "candidate_country": "USA", "candidate_latitude": 0.0})
        self.assertNotIn("candidate_latitude", result)
        lookup.assert_called_once_with("Troy", "", "USA")

    @patch("candidate_location_enrichment.lookup_city")
    def test_unsupported_country(self, lookup):
        result = enrich_candidate_location({"candidate_city": "Karachi", "candidate_country": "Pakistan"})
        self.assertNotIn("candidate_latitude", result)
        lookup.assert_not_called()

    @patch("candidate_location_enrichment.lookup_city")
    def test_missing_city(self, lookup):
        result = enrich_candidate_location({"candidate_city": "N/A", "candidate_country": "USA"})
        self.assertNotIn("candidate_longitude", result)
        lookup.assert_not_called()

    @patch("candidate_location_enrichment.lookup_city", side_effect=FileNotFoundError)
    def test_missing_reference_data(self, lookup):
        result = enrich_candidate_location({"candidate_city": "Ann Arbor", "candidate_state": "MI", "candidate_country": "USA"})
        self.assertNotIn("candidate_latitude", result)

    @patch("candidate_location_enrichment.lookup_city", return_value=RESOLVED)
    def test_extraction_to_coordinates(self, lookup):
        text = "Candidate Name\nToronto, ON, Canada\nEmail: candidate@example.com\nExperience\n"
        result = extract_and_enrich_candidate_location(text)
        self.assertEqual(result["candidate_city"], "Toronto")
        self.assertEqual(result["candidate_country"], "Canada")
        self.assertEqual(result["candidate_latitude"], 43.70643)

if __name__ == "__main__":
    unittest.main()
