"""Run: python -m unittest -v test_candidate_location_extractor.py"""
import unittest
from candidate_location_extractor import extract_candidate_location, COUNTRY_REGISTRY

class CandidateLocationTests(unittest.TestCase):
    def test_usa(self):
        r = extract_candidate_location('Alex Doe\nAnn Arbor, MI\nalex@example.com\nExperience\nToronto, ON')
        self.assertEqual((r['candidate_city'], r['candidate_state'], r['candidate_country']), ('Ann Arbor', 'MI', 'USA'))
    def test_canada(self):
        r = extract_candidate_location('Jane Doe\nLocation: Toronto, ON\nOpen to remote\nWilling to relocate')
        self.assertEqual(r['candidate_country'], 'Canada')
        self.assertEqual(r['remote_preference'], 'YES')
        self.assertEqual(r['relocation_willingness'], 'YES')
    def test_us_postal(self):
        self.assertEqual(extract_candidate_location('Name\nAustin, TX 78701')['candidate_country'], 'USA')
    def test_canadian_postal(self):
        self.assertEqual(extract_candidate_location('Name\nOttawa, ON K1A 0B1')['candidate_country'], 'Canada')
    def test_no_guess_from_employment(self):
        r = extract_candidate_location('Name\nSkills\n' + '\n'.join('Skill' for _ in range(18)) + '\nWorked in Toronto, ON')
        self.assertEqual(r['candidate_country'], 'N/A')
    def test_no_remote_from_employment(self):
        self.assertEqual(extract_candidate_location('Name\nWorked remotely for many years')['remote_preference'], 'N/A')
    def test_empty(self):
        self.assertEqual(extract_candidate_location(None)['candidate_location'], 'N/A')
    def test_new_country_registry_activation(self):
        COUNTRY_REGISTRY['United Kingdom'] = {'aliases': ('UK', 'United Kingdom')}
        try:
            r = extract_candidate_location('Name\nLondon, England, UK')
            self.assertEqual(r['candidate_country'], 'United Kingdom')
        finally:
            del COUNTRY_REGISTRY['United Kingdom']

if __name__ == '__main__':
    unittest.main()
