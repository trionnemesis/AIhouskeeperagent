"""ETL 排程純函式測試（REQ:DEPLOY:SCHED）。plvr 每旬發布 1/11/21；新鮮度監控 DI-9。"""
import unittest
from datetime import date

from lvr_mcp.schedule import next_publication_date, is_stale, season_for


class TestNextPublication(unittest.TestCase):
    def test_mid_month_to_11(self):
        self.assertEqual(next_publication_date(date(2026, 6, 5)), date(2026, 6, 11))

    def test_on_publication_day_returns_next(self):
        # 發布日當天 → 回「之後」的下一個（嚴格大於）
        self.assertEqual(next_publication_date(date(2026, 6, 11)), date(2026, 6, 21))
        self.assertEqual(next_publication_date(date(2026, 6, 1)), date(2026, 6, 11))

    def test_after_21_rolls_to_next_month(self):
        self.assertEqual(next_publication_date(date(2026, 6, 21)), date(2026, 7, 1))
        self.assertEqual(next_publication_date(date(2026, 6, 25)), date(2026, 7, 1))

    def test_year_boundary(self):
        self.assertEqual(next_publication_date(date(2026, 12, 21)), date(2027, 1, 1))


class TestFreshness(unittest.TestCase):
    def test_stale_beyond_max_age(self):
        self.assertTrue(is_stale(date(2026, 6, 1), date(2026, 6, 20), max_age_days=15))

    def test_fresh_within_max_age(self):
        self.assertFalse(is_stale(date(2026, 6, 1), date(2026, 6, 20), max_age_days=30))

    def test_boundary_equal_not_stale(self):
        # 剛好等於上限 → 尚未過期
        self.assertFalse(is_stale(date(2026, 6, 1), date(2026, 6, 16), max_age_days=15))


class TestSeasonFor(unittest.TestCase):
    def test_quarter_mapping(self):
        self.assertEqual(season_for(date(2026, 6, 15)), "115S2")   # 民國115 Q2
        self.assertEqual(season_for(date(2026, 1, 1)), "115S1")
        self.assertEqual(season_for(date(2026, 12, 31)), "115S4")


if __name__ == "__main__":
    unittest.main()
