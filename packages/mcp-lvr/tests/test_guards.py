"""LVR guards 測試 — Inv-4。測試向量手算，today='2026-06-20'（today+90='2026-09-18'）。"""

import unittest

from lvr_mcp.guards import net_unit_price, timestamp_guard


class TimestampGuardTest(unittest.TestCase):
    def test_keeps_only_in_range_dates(self):
        rows = [
            {"trade_date": "2026-03-05"},  # 範圍內 → 留
            {"trade_date": "2101-10-17"},  # 超上界 → 剔
            {"trade_date": "1921-01-28"},  # 早於下界 → 剔
            {"trade_date": "2009-12-31"},  # 下界前一天 → 剔
            {"trade_date": "2010-01-01"},  # 下界邊界 → 留
            {"trade_date": "2026-09-18"},  # 上界邊界(today+90) → 留
            {"trade_date": "2026-09-19"},  # 上界後一天 → 剔
        ]
        result = timestamp_guard(rows, "2026-06-20")
        kept = {r["trade_date"] for r in result}
        self.assertEqual(kept, {"2026-03-05", "2010-01-01", "2026-09-18"})
        self.assertEqual(len(result), 3)

    def test_drops_unparseable(self):
        rows = [{"trade_date": "not-a-date"}, {"trade_date": "2026-03-05"}]
        result = timestamp_guard(rows, "2026-06-20")
        self.assertEqual([r["trade_date"] for r in result], ["2026-03-05"])


class NetUnitPriceTest(unittest.TestCase):
    def test_computes_net_unit_price(self):
        self.assertEqual(net_unit_price(20000000, 2000000, 30), 600000.0)

    def test_zero_area_returns_none(self):
        self.assertIsNone(net_unit_price(1, 1, 0))

    def test_negative_area_returns_none(self):
        self.assertIsNone(net_unit_price(1000, 0, -5))


if __name__ == "__main__":
    unittest.main()
