import unittest

from public_safety_mcp.ingest import (
    parse_crime_csv,
    aggregate_crime,
    aggregate_crime_all,
    ingest_crime,
    parse_accidents_csv,
)

# 首列 keys + 第二列中文標籤(跳過) + 資料
SAMPLE = "\n".join([
    "type,oc_year,oc_data,oc_county,oc_region",
    "案類,發生年度,發生日期,發生縣市,發生鄉鎮市區",
    "住宅竊盜,115,0701,台北市,信義區",
    "住宅竊盜,115,0805,台北市,信義區",
    "汽車竊盜,115,0901,台北市,信義區",
    "住宅竊盜,115,0902,高雄市,苓雅區",
])


class TestParseCrime(unittest.TestCase):
    def test_parse(self):
        rows = parse_crime_csv(SAMPLE)
        self.assertEqual(len(rows), 4)  # 跳過中文標籤列
        self.assertEqual(rows[0]["type"], "住宅竊盜")
        self.assertEqual(rows[0]["oc_region"], "信義區")


class TestAggregate(unittest.TestCase):
    def test_area_level_counts(self):
        rows = parse_crime_csv(SAMPLE)
        stats = aggregate_crime(rows, "台北市", "信義區")
        by = {s["category"]: s["count"] for s in stats}
        self.assertEqual(by["住宅竊盜"], 2)
        self.assertEqual(by["汽車竊盜"], 1)
        self.assertNotIn("高雄市", str(stats))  # 只含該區

    def test_di5_no_coordinates(self):
        rows = parse_crime_csv(SAMPLE)
        stats = aggregate_crime(rows, "台北市", "信義區")
        # DI-5：輸出僅 category/count/period，不得含座標/門牌
        for s in stats:
            self.assertNotIn("lat", s)
            self.assertNotIn("lng", s)
            self.assertNotIn("address", s)


class TestIngestDI(unittest.TestCase):
    def test_di_fetcher(self):
        rows = ingest_crime(lambda _url: SAMPLE, "http://fake")
        self.assertEqual(len(rows), 4)


class TestAggregateAll(unittest.TestCase):
    def test_groups_every_county_region(self):
        rows = parse_crime_csv(SAMPLE)
        groups = aggregate_crime_all(rows)
        keyed = {(g["county"], g["region"]): g for g in groups}
        self.assertIn(("台北市", "信義區"), keyed)
        self.assertIn(("高雄市", "苓雅區"), keyed)        # 全行政區，非單一
        tp = {s["category"]: s["count"] for s in keyed[("台北市", "信義區")]["stats"]}
        self.assertEqual(tp["住宅竊盜"], 2)

    def test_no_coordinates_in_groups(self):
        groups = aggregate_crime_all(parse_crime_csv(SAMPLE))
        self.assertNotIn("lat", str(groups))      # DI-5：區域級
        self.assertNotIn("lng", str(groups))


# NPA A1/A2 事故 CSV（首列中文表頭 + 資料）；A1/A2 由檔/參數帶入，列含經緯度
ACC_SAMPLE = "\n".join([
    "發生年度,發生月,發生日,經度,緯度",
    "115,7,1,121.5654,25.0330",
    "115,7,2,121.5000,25.0030",
    "115,7,3,,",            # 缺座標 → 略過
])


class TestParseAccidents(unittest.TestCase):
    def test_parse_points_with_severity(self):
        rows = parse_accidents_csv(ACC_SAMPLE, severity="A1")
        self.assertEqual(len(rows), 2)            # 缺座標列被略過
        self.assertEqual(rows[0]["severity"], "A1")
        self.assertAlmostEqual(rows[0]["lat"], 25.0330)
        self.assertAlmostEqual(rows[0]["lng"], 121.5654)
        self.assertEqual(rows[0]["occurred_at"], "2026-07-01")  # ROC→ISO

    def test_invalid_coords_skipped(self):
        rows = parse_accidents_csv(ACC_SAMPLE, severity="A2")
        self.assertTrue(all(r["lat"] and r["lng"] for r in rows))


if __name__ == "__main__":
    unittest.main()
