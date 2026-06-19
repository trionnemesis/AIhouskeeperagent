"""LVR service 測試 — Inv-5（拒答優於猜測）。today='2026-06-20'。"""

import unittest

from lvr_mcp.service import query_market


def _row(d):
    return {"trade_date": d}


class QueryMarketTest(unittest.TestCase):
    def test_refused_when_insufficient_comps(self):
        # 只有 2 筆有效（2026-09-19 超上界被剔）
        rows = [_row("2026-03-05"), _row("2010-01-01"), _row("2026-09-19")]
        result = query_market(rows, "2026-06-20")
        self.assertEqual(
            result, {"outcome": "refused", "reason": "insufficient_comps"}
        )

    def test_provided_when_enough_comps(self):
        rows = [_row("2026-03-05"), _row("2010-01-01"), _row("2026-09-18")]
        result = query_market(rows, "2026-06-20")
        self.assertEqual(result["outcome"], "provided")
        self.assertEqual(result["n"], 3)
        self.assertEqual(len(result["comps"]), 3)
        self.assertEqual(result["data_as_of"], "2026-06")
        self.assertEqual(result["source"], "內政部不動產交易實價查詢服務網")


if __name__ == "__main__":
    unittest.main()
