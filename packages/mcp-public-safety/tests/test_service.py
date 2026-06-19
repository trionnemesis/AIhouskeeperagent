import unittest

from public_safety_mcp.service import area_crime_stats, traffic_accident_density


class TestTrafficAccidentDensity(unittest.TestCase):
    def test_provided_aggregated_only(self):
        result = traffic_accident_density(
            [{"severity": "A2", "lat": 25.0, "lng": 121.5}], 25.0, 121.5, 500
        )
        self.assertEqual(result["outcome"], "provided")
        self.assertEqual(result["density"]["total_n"], 1)
        self.assertEqual(result["source"], "內政部警政署")

    def test_no_individual_points_in_output(self):
        # DI-5: 輸出不得含個別事故點座標
        result = traffic_accident_density(
            [{"severity": "A2", "lat": 25.033, "lng": 121.565}], 25.0, 121.5, 500
        )
        self.assertNotIn("points", result)
        self.assertNotIn("points", result["density"])
        self.assertNotIn("lat", result["density"])
        self.assertNotIn("lng", result["density"])

    def test_empty_points_refused(self):
        result = traffic_accident_density([], 25.0, 121.5, 500)
        self.assertEqual(
            result, {"outcome": "refused", "reason": "insufficient_data"}
        )


class TestAreaCrimeStats(unittest.TestCase):
    def test_too_fine_refused(self):
        result = area_crime_stats({"address": "信義路五段7號"}, [])
        self.assertEqual(
            result, {"outcome": "refused", "reason": "granularity_too_fine"}
        )

    def test_district_provided(self):
        result = area_crime_stats(
            {"district": "信義區"}, [{"category": "竊盜", "count": 5}]
        )
        self.assertEqual(result["outcome"], "provided")
        self.assertEqual(result["granularity"], "鄉鎮市區")
        self.assertEqual(result["stats"], [{"category": "竊盜", "count": 5}])
        self.assertEqual(result["source"], "內政部警政署")


if __name__ == "__main__":
    unittest.main()
