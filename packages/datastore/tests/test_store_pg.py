"""datastore PostgreSQL 後端測試（CR-2026-008）。需 DATABASE_URL=postgresql://...，否則 skip。
驗證 PG dialect（ON CONFLICT DO NOTHING / %s 佔位 / dict_row）行為與 SQLite 一致。"""
import os
import unittest

from datastore import store

URL = os.environ.get("DATABASE_URL", "")
_TS = "2026-06-20T06:00:00+08:00"


@unittest.skipUnless(URL.startswith(("postgres://", "postgresql://")), "需 DATABASE_URL=postgresql://...")
class TestStorePostgres(unittest.TestCase):
    def setUp(self):
        self.conn = store.connect(URL)
        store.init_schema(self.conn)
        for t in ("lvr_trades", "crime_area_stats", "traffic_accidents", "provenance"):
            self.conn.execute(f"TRUNCATE {t} RESTART IDENTITY")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_lvr_upsert_query_dedup_provenance(self):
        rows = [
            {"district": "信義區", "trade_date": "2026-01-15", "total_price": 20000000,
             "area_ping": 30.0, "unit_price_net": 666666.0, "parking_price": 0,
             "building_type": "成屋", "deal_type": "sale"},
            {"district": "中山區", "trade_date": "2026-02-10", "total_price": 18000000,
             "area_ping": 25.0, "unit_price_net": 720000.0, "parking_price": 0,
             "building_type": "成屋", "deal_type": "sale"},
        ]
        n = store.upsert_lvr_trades(self.conn, rows, source="內政部", data_as_of="2026S1", ingested_at=_TS)
        self.assertEqual(n, 2)
        n2 = store.upsert_lvr_trades(self.conn, rows, source="內政部", data_as_of="2026S1", ingested_at=_TS)
        self.assertEqual(n2, 0)  # ON CONFLICT DO NOTHING → 去重
        got = store.query_lvr_comps(self.conn, "信義區")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["trade_date"], "2026-01-15")
        self.assertEqual(got[0]["district"], "信義區")
        prov = store.query_provenance(self.conn, "lvr_trade")
        self.assertGreaterEqual(len(prov), 1)
        self.assertEqual(prov[0]["authority"], "gov")

    def test_crime_area(self):
        stats = [{"category": "竊盜", "count": 5, "period": "115"},
                 {"category": "詐欺", "count": 3, "period": "115"}]
        store.upsert_crime_area_stats(self.conn, "湖口鄉", stats, source="警政署", as_of="2026", ingested_at=_TS)
        got = store.query_crime_stats(self.conn, "湖口鄉")
        self.assertEqual(len(got), 2)
        cols = {r["column_name"] for r in self.conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='crime_area_stats'"
        ).fetchall()}
        self.assertNotIn("lat", cols)  # DI-5
        self.assertNotIn("lng", cols)

    def test_traffic_radius_precise(self):
        pts = [
            {"lat": 25.000, "lng": 121.500, "severity": "A1", "occurred_at": "2026-07-01"},
            {"lat": 25.003, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-02"},
            {"lat": 25.050, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-03"},  # bbox 外
            {"lat": 25.004, "lng": 121.504, "severity": "A2", "occurred_at": "2026-07-04"},  # bbox 內半徑外
        ]
        store.upsert_traffic_accidents(self.conn, pts, source="警政署", as_of="2026", ingested_at=_TS)
        near = store.query_accident_points_near(self.conn, 25.000, 121.500, 500)
        self.assertEqual(len(near), 2)
        self.assertEqual(len(store.query_accident_points_near(self.conn, 25.000, 121.500, 10000)), 4)


if __name__ == "__main__":
    unittest.main()
