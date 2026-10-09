"""Run: python -m unittest -v test_candidate_location_extractor.py"""
import unittest
from candidate_location_extractor import (
    extract_candidate_location, COUNTRY_REGISTRY,
    SEARCH_ENABLED_COUNTRIES, is_country_search_enabled,
)


class CandidateLocationTests(unittest.TestCase):
    def extract(self, line):
        return extract_candidate_location("Candidate Name\n" + line + "\nemail@example.com")

    def test_usa(self):
        r = extract_candidate_location("Name\nAnn Arbor, MI\nExperience\nToronto, ON")
        self.assertEqual((r["candidate_city"], r["candidate_state"], r["candidate_country"]), ("Ann Arbor", "MI", "USA"))

    def test_canada(self):
        r = extract_candidate_location("Jane\nToronto, ON\nOpen to remote\nWilling to relocate")
        self.assertEqual(r["candidate_country"], "Canada")
        self.assertEqual((r["remote_preference"], r["relocation_willingness"]), ("YES", "YES"))

    def test_us_postal(self):
        self.assertEqual(self.extract("Austin, TX 78701")["candidate_postal_code"], "78701")

    def test_canadian_postal(self):
        r = self.extract("Ottawa, ON K1A 0B1")
        self.assertEqual((r["candidate_country"], r["candidate_postal_code"]), ("Canada", "K1A 0B1"))

    def test_canadian_full_street_address(self):
        r = self.extract("3724 Crabtree Crescent, Mississauga, Ontario, Canada L4T-1S6")
        self.assertEqual((r["candidate_city"], r["candidate_state"], r["candidate_country"]), ("Mississauga", "Ontario", "Canada"))
        self.assertEqual(r["candidate_postal_code"], "L4T 1S6")
        self.assertEqual(r["candidate_location"], "Mississauga, Ontario, Canada")
        self.assertTrue(r["candidate_address"].startswith("3724 Crabtree"))

    def test_greater_toronto_area(self):
        self.assertEqual(self.extract("Greater Toronto Area")["candidate_city"], "Greater Toronto Area")

    def test_canada_ab(self):
        r = self.extract("Canada, AB")
        self.assertEqual((r["candidate_city"], r["candidate_state"], r["candidate_country"]), ("N/A", "AB", "Canada"))

    def test_ca_country_versus_california(self):
        self.assertEqual(self.extract("Toronto, ON, CA")["candidate_country"], "Canada")
        self.assertEqual(self.extract("San Francisco, CA")["candidate_country"], "USA")
        self.assertEqual(self.extract("Los Angeles, CA, USA")["candidate_country"], "USA")

    def test_international_extraction_without_search_activation(self):
        r = self.extract("Karachi, Sindh, Pakistan")
        self.assertEqual((r["candidate_city"], r["candidate_country"]), ("Karachi", "Pakistan"))
        self.assertFalse(is_country_search_enabled("Pakistan"))
        self.assertTrue(is_country_search_enabled("Canada"))

    def test_new_country_registry(self):
        COUNTRY_REGISTRY["Australia"] = {"aliases": ("Australia", "AU")}
        try:
            self.assertEqual(self.extract("Sydney, NSW, Australia")["candidate_country"], "Australia")
            self.assertFalse(is_country_search_enabled("Australia"))
        finally:
            del COUNTRY_REGISTRY["Australia"]

    def test_no_guess_from_employment(self):
        r = extract_candidate_location("Name\nSkills\n" + "\n".join("Skill" for _ in range(18)) + "\nWorked in Toronto, ON")
        self.assertEqual(r["candidate_country"], "N/A")

    def test_no_remote_from_employment(self):
        self.assertEqual(self.extract("Worked remotely for many years")["remote_preference"], "N/A")


    def test_oakville_postal_before_country(self):
        r = self.extract("3724 Grand Oak Trail, Oakville, Ontario L6M 4T1, Canada.")
        self.assertEqual((r["candidate_city"], r["candidate_postal_code"]), ("Oakville", "L6M 4T1"))
        self.assertNotEqual(r["candidate_address"], "N/A")

    def test_toronto_contact_line(self):
        r = self.extract("name@example.com 416-555-1234 Toronto, ON github.com/name")
        self.assertEqual((r["candidate_city"], r["candidate_country"]), ("Toronto", "Canada"))

    def test_toronto_icon_line(self):
        r = self.extract("♂location-arrowToronto, ON♂phone249-535-2804 /envel name@example.com")
        self.assertEqual((r["candidate_city"], r["candidate_country"]), ("Toronto", "Canada"))

    def test_nigeria_fct_abuja(self):
        r = self.extract("FCT-Abuja, Nigeria")
        self.assertEqual((r["candidate_city"], r["candidate_state"], r["candidate_country"]), ("Abuja", "FCT", "Nigeria"))

    def test_burlington_label_contact_line(self):
        r = self.extract("Khyati Dahale Email: person@example.com Location: Burlington, Ontario Phone: 416-555-2233")
        self.assertEqual((r["candidate_city"], r["candidate_country"]), ("Burlington", "Canada"))

    def test_hamilton_pipe_contact_line(self):
        r = self.extract("416-555-1234 | name@example.com | Hamilton, Ontario | linkedin.com/in/name")
        self.assertEqual((r["candidate_city"], r["candidate_country"]), ("Hamilton", "Canada"))

    def test_empty(self):
        self.assertEqual(extract_candidate_location(None)["candidate_location"], "N/A")


if __name__ == "__main__":
    unittest.main()
