"""datastore 落地測試（REQ:DEPLOY:STORE）。erd.dbml 快取表的 SQLite 實現。
in-memory 連線；ingested_at 以 DI 注入（時間可測）。"""
import unittest

from datastore import store

_TS = "2026-06-20T06:00:00+08:00"


def _conn():
    c = store.connect(":memory:")
    store.init_schema(c)
    return c


class TestLvrTrades(unittest.TestCase):
    def test_upsert_then_query_by_district(self):
        conn = _conn()
        rows = [
            {"district": "信義區", "trade_date": "2026-01-15", "total_price": 20000000,
             "area_ping": 30.0, "unit_price_net": 666666.0, "parking_price": 0,
             "building_type": "成屋", "deal_type": "sale"},
            {"district": "中山區", "trade_date": "2026-02-10", "total_price": 18000000,
             "area_ping": 25.0, "unit_price_net": 720000.0, "parking_price": 0,
             "building_type": "成屋", "deal_type": "sale"},
        ]
        n = store.upsert_lvr_trades(conn, rows, source="內政部不動產交易實價查詢服務網",
                                    data_as_of="2026-06", ingested_at=_TS)
        self.assertEqual(n, 2)
        got = store.query_lvr_comps(conn, "信義區")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["trade_date"], "2026-01-15")
        self.assertEqual(got[0]["district"], "信義區")

    def test_dedup_idempotent(self):
        conn = _conn()
        row = [{"district": "信義區", "trade_date": "2026-01-15", "total_price": 20000000,
                "area_ping": 30.0, "unit_price_net": 666666.0, "parking_price": 0,
                "building_type": "成屋", "deal_type": "sale"}]
        store.upsert_lvr_trades(conn, row, source="s", data_as_of="2026-06", ingested_at=_TS)
        store.upsert_lvr_trades(conn, row, source="s", data_as_of="2026-06", ingested_at=_TS)
        self.assertEqual(len(store.query_lvr_comps(conn, "信義區")), 1)  # 去重，不重複落地

    def test_provenance_recorded_on_upsert(self):
        conn = _conn()
        store.upsert_lvr_trades(conn, [{"district": "信義區", "trade_date": "2026-01-15",
                                        "total_price": 1, "area_ping": 1.0, "unit_price_net": 1.0,
                                        "parking_price": 0, "building_type": "成屋", "deal_type": "sale"}],
                                source="內政部", data_as_of="2026-06", ingested_at=_TS)
        prov = store.query_provenance(conn, "lvr_trade")
        self.assertGreaterEqual(len(prov), 1)
        self.assertEqual(prov[0]["authority"], "gov")  # DI-7：政府源權威度


class TestCrimeAreaStats(unittest.TestCase):
    def test_upsert_then_query(self):
        conn = _conn()
        stats = [{"category": "竊盜", "count": 5, "period": "115"},
                 {"category": "詐欺", "count": 3, "period": "115"}]
        store.upsert_crime_area_stats(conn, "湖口鄉", stats, source="內政部警政署",
                                      as_of="2026", ingested_at=_TS)
        got = store.query_crime_stats(conn, "湖口鄉")
        self.assertEqual(len(got), 2)
        self.assertTrue(all("count" in s and "category" in s for s in got))

    def test_di5_no_coordinates_columns(self):
        # DI-5：crime_area_stats 不得有座標欄（區域級封頂）
        conn = _conn()
        cols = {r[1] for r in conn.execute("PRAGMA table_info(crime_area_stats)").fetchall()}
        self.assertNotIn("lat", cols)
        self.assertNotIn("lng", cols)


class TestTrafficAccidents(unittest.TestCase):
    # 中心 (25.000, 121.500)；P1 同點(in)、P2 ~333m(in)、P3 ~5.5km(bbox 即排除)、
    # P4 角點 ~600m：在 500m bbox 內但半徑外 → 只有 haversine 能排除（守住精篩）。
    POINTS = [
        {"lat": 25.000, "lng": 121.500, "severity": "A1", "occurred_at": "2026-07-01"},
        {"lat": 25.003, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-02"},
        {"lat": 25.050, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-03"},
        {"lat": 25.004, "lng": 121.504, "severity": "A2", "occurred_at": "2026-07-04"},
    ]

    def test_query_points_within_radius_only(self):
        conn = _conn()
        store.upsert_traffic_accidents(conn, self.POINTS, source="內政部警政署",
                                       as_of="2026", ingested_at=_TS)
        near = store.query_accident_points_near(conn, 25.000, 121.500, 500)
        self.assertEqual(len(near), 2)          # P3(bbox外) + P4(bbox內半徑外) 皆排除
        sev = sorted(p["severity"] for p in near)
        self.assertEqual(sev, ["A1", "A2"])

    def test_wider_radius_includes_all(self):
        conn = _conn()
        store.upsert_traffic_accidents(conn, self.POINTS, source="s", as_of="2026", ingested_at=_TS)
        self.assertEqual(len(store.query_accident_points_near(conn, 25.000, 121.500, 10000)), 4)

    def test_dedup_idempotent(self):
        conn = _conn()
        store.upsert_traffic_accidents(conn, self.POINTS, source="s", as_of="2026", ingested_at=_TS)
        store.upsert_traffic_accidents(conn, self.POINTS, source="s", as_of="2026", ingested_at=_TS)
        self.assertEqual(len(store.query_accident_points_near(conn, 25.000, 121.500, 10000)), 4)


if __name__ == "__main__":
    unittest.main()
