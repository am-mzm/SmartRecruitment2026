import unittest
from candidate_geographic_search import haversine_miles, location_match, sort_skills_first


class GeographicSearchTests(unittest.TestCase):
    def test_zero_distance(self):
        self.assertAlmostEqual(haversine_miles(42.2808, -83.7430, 42.2808, -83.7430), 0)

    def test_city_within_200(self):
        c = {'candidate_country': 'USA', 'candidate_state': 'MI', 'candidate_latitude': 42.3314, 'candidate_longitude': -83.0458}
        match, distance = location_match(c, city='Ann Arbor', center=(42.2808, -83.7430))
        self.assertTrue(match)
        self.assertGreater(distance, 0)

    def test_city_outside_200(self):
        c = {'candidate_country': 'USA', 'candidate_state': 'IL', 'candidate_latitude': 41.8781, 'candidate_longitude': -87.6298}
        self.assertFalse(location_match(c, city='Ann Arbor', center=(42.2808, -83.7430))[0])

    def test_city_needs_resolved_center(self):
        with self.assertRaises(ValueError):
            location_match({}, city='Springfield')

    def test_missing_coords_not_assumed_inside_radius(self):
        self.assertFalse(location_match({'candidate_city': 'Ann Arbor'}, city='Ann Arbor', center=(42.2808, -83.7430))[0])

    def test_state_query_no_radius(self):
        self.assertTrue(location_match({'candidate_country':'USA','candidate_state':'Michigan'}, state='MI')[0])

    def test_country_query_no_radius(self):
        self.assertTrue(location_match({'candidate_country':'Canada'}, country='CAN')[0])

    def test_country_excluded(self):
        self.assertFalse(location_match({'candidate_country':'USA'}, country='Canada')[0])

    def test_country_disabled(self):
        with self.assertRaises(ValueError):
            location_match({}, country='Pakistan')

    def test_state_country_both_required(self):
        self.assertTrue(location_match({'candidate_country':'Canada','candidate_state':'ON'}, state='Ontario',country='Canada')[0])
        self.assertFalse(location_match({'candidate_country':'USA','candidate_state':'ON'}, state='Ontario',country='Canada')[0])

    def test_skills_first_distance_breaks_ties(self):
        c = [{'name':'A','relevance_score':95,'distance_miles':150},
             {'name':'B','relevance_score':90,'distance_miles':5},
             {'name':'C','relevance_score':95,'distance_miles':10}]
        self.assertEqual([v['name'] for v in sort_skills_first(c)], ['C','A','B'])

    def test_no_location_selected_unrestricted(self):
        self.assertTrue(location_match({})[0])

    def test_radius_boundary_inclusive(self):
        c={'candidate_latitude':0,'candidate_longitude':0}
        self.assertTrue(location_match(c,city='X',center=(0,0),radius_miles=1)[0])


if __name__ == '__main__':
    unittest.main()
