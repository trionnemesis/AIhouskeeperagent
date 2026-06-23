import io
import unittest
import zipfile

from lvr_mcp.ingest import (
    building_type_for,
    ingest_lvr,
    parse_lvr_csv,
    roc_to_iso,
)

# ── plvr 實檔欄位佈局（逐欄核對 115S1 兩檔）─────────────────────────────
# 成屋檔 a_lvr_land_a.csv：33 欄（不動產買賣）。
A_HEADER = [
    "鄉鎮市區", "交易標的", "土地位置建物門牌", "土地移轉總面積平方公尺", "都市土地使用分區",
    "非都市土地使用分區", "非都市土地使用編定", "交易年月日", "交易筆棟數", "移轉層次",
    "總樓層數", "建物型態", "主要用途", "主要建材", "建築完成年月",
    "建物移轉總面積平方公尺", "建物現況格局-房", "建物現況格局-廳", "建物現況格局-衛", "建物現況格局-隔間",
    "有無管理組織", "總價元", "單價元平方公尺", "車位類別", "車位移轉總面積平方公尺",
    "車位總價元", "備註", "編號", "主建物面積", "附屬建物面積",
    "陽台面積", "電梯", "移轉編號",
]
assert len(A_HEADER) == 33

# 預售屋檔 a_lvr_land_b.csv：31 欄（預售屋買賣）。欄位佈局與成屋檔**不同**：
#   - 建物移轉總面積 在 col13（成屋為 col15）
#   - 總價元 在 col19（成屋為 col21）；單價元 col20（成屋 col22）
#   - 車位總價元 在 col21 —— 正落在成屋「總價元」的固定索引上（→ 舊碼把車位價當總價）
#   - col15 在預售檔是「建物現況格局-廳」、col25 是「編號」（字串）→ 舊碼面積/車位讀到污染值
B_HEADER = [
    "鄉鎮市區", "交易標的", "土地位置建物門牌", "土地移轉總面積平方公尺", "都市土地使用分區",
    "主要用途", "主要建材", "交易年月日", "交易筆棟數", "移轉層次",
    "總樓層數", "建物型態", "建築完成年月", "建物移轉總面積平方公尺", "建物現況格局-房",
    "建物現況格局-廳", "建物現況格局-衛", "建物現況格局-隔間", "有無管理組織", "總價元",
    "單價元平方公尺", "車位總價元", "車位類別", "車位移轉總面積平方公尺", "備註",
    "編號", "建案名稱", "棟及號", "解約情形", "非都市土地使用分區",
    "附屬建物面積",
]
assert len(B_HEADER) == 31


def _build_csv(header: list[str], records: list[dict]) -> str:
    """組 plvr 風格 CSV：第 0 列中文表頭、第 1 列英文表頭(佔位)、其後資料列。"""
    lines = [",".join(header), ",".join(["e"] * len(header))]
    for rec in records:
        lines.append(",".join(str(rec.get(h, "x")) for h in header))
    return "\n".join(lines)


# 成屋：信義區一筆（無車位）
A_REC = {
    "鄉鎮市區": "信義區",
    "交易標的": "房地(土地+建物)",
    "交易年月日": "1150115",
    "建物移轉總面積平方公尺": "100.0",
    "總價元": "20000000",
    "單價元平方公尺": "200000",
    "車位總價元": "0",
}
A_CSV = _build_csv(A_HEADER, [A_REC])

# 預售：松山區一筆（含車位）。交易標的**不含「預售」字樣**（與實檔一致）。
B_REC = {
    "鄉鎮市區": "松山區",
    "交易標的": "房地(土地+建物)+車位",
    "交易年月日": "1150310",
    "建物移轉總面積平方公尺": "50.0",
    "建物現況格局-廳": "2",         # 落在成屋面積固定索引 col15 上
    "總價元": "30000000",
    "單價元平方公尺": "600000",
    "車位總價元": "2000000",        # 落在成屋總價固定索引 col21 上
    "車位類別": "坡道平面",
    "編號": "PRES000001",          # 落在成屋車位固定索引 col25 上
}
B_CSV = _build_csv(B_HEADER, [B_REC])


class TestRoc(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(roc_to_iso("1151024"), "2026-10-24")
        self.assertEqual(roc_to_iso("0991231"), "2010-12-31")  # 民國99

    def test_invalid(self):
        self.assertIsNone(roc_to_iso("bad"))
        self.assertIsNone(roc_to_iso(""))
        self.assertIsNone(roc_to_iso("1151340"))  # 13 月


class TestParseSale(unittest.TestCase):
    """成屋檔（33 欄）以中文表頭定位仍正確（無回歸）。"""

    def test_parse(self):
        rows = parse_lvr_csv(A_CSV)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["district"], "信義區")
        self.assertEqual(rows[0]["trade_date"], "2026-01-15")
        self.assertEqual(rows[0]["area_sqm"], 100.0)
        self.assertEqual(rows[0]["total_price"], 20000000)
        self.assertEqual(rows[0]["unit_price_sqm"], 200000)
        self.assertEqual(rows[0]["parking_price"], 0)


class TestParsePresale(unittest.TestCase):
    """Bug 2 — 預售檔（31 欄）佈局不同，固定索引會錯位；須以表頭動態定位。"""

    def test_layout_differs_from_sale(self):
        # 反證：成屋 schema 的固定索引在預售檔落在別的欄
        self.assertNotEqual(B_HEADER[15], "建物移轉總面積平方公尺")
        self.assertEqual(B_HEADER[21], "車位總價元")  # 成屋「總價元」索引在預售檔是車位價
        self.assertEqual(B_HEADER[25], "編號")

    def test_header_aligned_values(self):
        rows = parse_lvr_csv(B_CSV)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["district"], "松山區")
        self.assertEqual(r["trade_date"], "2026-03-10")
        # 以表頭定位 → 對齊；若沿用成屋固定索引 col15/21/22/25 會得 2.0 / 2000000 / 0 / 0
        self.assertEqual(r["area_sqm"], 50.0)
        self.assertEqual(r["total_price"], 30000000)
        self.assertEqual(r["unit_price_sqm"], 600000)
        self.assertEqual(r["parking_price"], 2000000)

    def test_not_contaminated_by_fixed_index(self):
        # 明示舊固定索引的污染值，鎖死回歸
        r = parse_lvr_csv(B_CSV)[0]
        self.assertNotEqual(r["area_sqm"], 2.0)            # col15=建物現況格局-廳
        self.assertNotEqual(r["total_price"], 2000000)     # col21=車位總價元
        self.assertNotEqual(r["parking_price"], 0)         # col25=編號(字串)


class TestBuildingType(unittest.TestCase):
    """Bug 1 — 預售/成屋依來源檔名判別，而非交易標的字串。"""

    def test_by_filename(self):
        self.assertEqual(building_type_for("a_lvr_land_a.csv"), "成屋")
        self.assertEqual(building_type_for("a_lvr_land_b.csv"), "預售")
        self.assertEqual(building_type_for("f_lvr_land_b.csv"), "預售")  # 縣市前綴不影響
        self.assertEqual(building_type_for("e_lvr_land_a.csv"), "成屋")

    def test_deal_target_lacks_presale_keyword(self):
        # 預售檔交易標的不含「預售」→ 舊「'預售' in deal_target」判別恆 False
        r = parse_lvr_csv(B_CSV)[0]
        self.assertNotIn("預售", r["deal_target"])


class TestIngestDI(unittest.TestCase):
    def _zip(self, files: dict[str, str]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, text in files.items():
                z.writestr(name, text)
        return buf.getvalue()

    def test_di_fetcher_annotates_building_type(self):
        zbytes = self._zip({"a_lvr_land_a.csv": A_CSV, "a_lvr_land_b.csv": B_CSV})

        def fake_fetcher(_season: str) -> bytes:
            return zbytes

        rows = ingest_lvr(fake_fetcher, "115S1",
                          ["a_lvr_land_a.csv", "a_lvr_land_b.csv"])
        self.assertEqual(len(rows), 2)
        by_district = {r["district"]: r for r in rows}
        self.assertEqual(by_district["信義區"]["building_type"], "成屋")
        self.assertEqual(by_district["松山區"]["building_type"], "預售")
        # 預售筆欄位對齊（非污染）
        self.assertEqual(by_district["松山區"]["area_sqm"], 50.0)
        self.assertEqual(by_district["松山區"]["total_price"], 30000000)
        self.assertEqual(by_district["松山區"]["parking_price"], 2000000)

    def test_sale_only_still_works(self):
        # 目前部署規避法：只灌成屋檔，仍正常且標成屋
        zbytes = self._zip({"a_lvr_land_a.csv": A_CSV})

        def fake_fetcher(_season: str) -> bytes:
            return zbytes

        rows = ingest_lvr(fake_fetcher, "115S1", ["a_lvr_land_a.csv"])
        self.assertEqual(len(rows), 1)
        self.assertTrue(all(r["building_type"] == "成屋" for r in rows))


class TestHeaderDrift(unittest.TestCase):
    """表頭以名稱定位後，成屋檔 ingest 即依賴表頭字串 → 須(a)容忍真實單位記法、
    (b)無法辨識時安全回空且**出聲**（不靜默歸零，避免既有成屋路徑無聲回歸）。"""

    def test_unit_notation_variants_resolve(self):
        # plvr 實檔單位曾以「㎡」符號（見舊 docstring）及括號/斜線記法出現
        header = list(A_HEADER)
        header[15] = "建物移轉總面積(㎡)"   # 括號 + ㎡
        header[22] = "單價元/㎡"            # 斜線 + ㎡
        rec = {
            "鄉鎮市區": "中山區", "交易標的": "房地(土地+建物)", "交易年月日": "1150620",
            "建物移轉總面積(㎡)": "120.0", "總價元": "24000000",
            "單價元/㎡": "200000", "車位總價元": "0",
        }
        rows = parse_lvr_csv(_build_csv(header, [rec]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["area_sqm"], 120.0)
        self.assertEqual(rows[0]["total_price"], 24000000)
        self.assertEqual(rows[0]["unit_price_sqm"], 200000)

    def test_unrecognized_header_returns_empty(self):
        bogus = "\n".join(["欄A,欄B,欄C", "a,b,c", "1,2,3"])
        self.assertEqual(parse_lvr_csv(bogus), [])

    def test_ingest_warns_when_present_file_yields_zero(self):
        # 檔在 ZIP 內但表頭無法辨識 → 0 筆 → 必須 WARNING（部署日誌/CI 可偵測漂移）
        bogus_csv = "\n".join(["欄A,欄B", "a,b", "1,2"])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("a_lvr_land_a.csv", bogus_csv)
        zbytes = buf.getvalue()
        with self.assertLogs("lvr_mcp.ingest", level="WARNING") as cm:
            rows = ingest_lvr(lambda _s: zbytes, "115S1", ["a_lvr_land_a.csv"])
        self.assertEqual(rows, [])
        self.assertTrue(any("a_lvr_land_a.csv" in line for line in cm.output))


if __name__ == "__main__":
    unittest.main()
