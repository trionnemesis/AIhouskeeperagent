import unittest

from public_safety_mcp.ingest import parse_crime_csv, aggregate_crime, ingest_crime

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


if __name__ == "__main__":
    unittest.main()
