import unittest

from public_safety_mcp.guards import (
    aggregate_density,
    assert_area_granularity,
    contains_negative_label,
)


class TestAggregateDensity(unittest.TestCase):
    def test_severity_mix_and_total(self):
        result = aggregate_density(
            [{"severity": "A1"}, {"severity": "A2"}, {"severity": "A2"}]
        )
        self.assertEqual(
            result, {"total_n": 3, "severity_mix": {"A1": 1, "A2": 2}}
        )

    def test_no_individual_point_keys_leaked(self):
        # DI-5: 聚合結果不得含個別點座標/地址
        result = aggregate_density([{"severity": "A2", "lat": 25.0, "lng": 121.5}])
        self.assertNotIn("points", result)
        self.assertNotIn("lat", result)
        self.assertNotIn("lng", result)
        self.assertNotIn("address", result)

    def test_empty_points(self):
        result = aggregate_density([])
        self.assertEqual(result, {"total_n": 0, "severity_mix": {}})


class TestContainsNegativeLabel(unittest.TestCase):
    def test_positive_treat_diff(self):
        self.assertIs(contains_negative_label("這區治安差"), True)

    def test_negative_neutral(self):
        self.assertIs(contains_negative_label("生活機能佳"), False)

    def test_other_negative_terms(self):
        self.assertIs(contains_negative_label("高犯罪區域"), True)
        self.assertIs(contains_negative_label("這裡是嫌惡設施"), True)
        self.assertIs(contains_negative_label("治安不好"), True)


class TestAssertAreaGranularity(unittest.TestCase):
    def test_district_ok(self):
        # 不應拋出例外
        self.assertIsNone(assert_area_granularity({"district": "信義區"}))

    def test_address_too_fine(self):
        with self.assertRaises(ValueError) as ctx:
            assert_area_granularity({"address": "信義路五段7號"})
        self.assertEqual(str(ctx.exception), "GRANULARITY_TOO_FINE")

    def test_parcel_too_fine(self):
        with self.assertRaises(ValueError):
            assert_area_granularity({"parcel": "信義段三小段123地號"})

    def test_listing_id_too_fine(self):
        with self.assertRaises(ValueError):
            assert_area_granularity({"listing_id": "L-0001"})


if __name__ == "__main__":
    unittest.main()
