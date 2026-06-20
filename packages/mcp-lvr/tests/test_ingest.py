import io
import ssl
import unittest
import zipfile

from lvr_mcp.ingest import roc_to_iso, parse_lvr_csv, ingest_lvr, build_secure_ssl_context


def _row(district, target, rocdate, area, total, unitsqm, parking):
    f = [""] * 26
    f[0], f[1], f[7], f[15], f[21], f[22], f[25] = district, target, rocdate, area, total, unitsqm, parking
    return ",".join(f)


# 兩列表頭（中/英）+ 兩筆資料（手算向量）
SAMPLE = "\n".join([
    "鄉鎮市區,交易標的," + ",".join(["c"] * 24),
    "district,sign," + ",".join(["e"] * 24),
    _row("信義區", "房地(土地+建物)", "1150115", "100.0", "20000000", "200000", "0"),
    _row("南港區", "房地(土地+建物)", "1151024", "80.0", "16000000", "200000", "2000000"),
])


class TestRoc(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(roc_to_iso("1151024"), "2026-10-24")
        self.assertEqual(roc_to_iso("0991231"), "2010-12-31")  # 民國99

    def test_invalid(self):
        self.assertIsNone(roc_to_iso("bad"))
        self.assertIsNone(roc_to_iso(""))
        self.assertIsNone(roc_to_iso("1151340"))  # 13 月


class TestParse(unittest.TestCase):
    def test_parse(self):
        rows = parse_lvr_csv(SAMPLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["district"], "信義區")
        self.assertEqual(rows[0]["trade_date"], "2026-01-15")
        self.assertEqual(rows[0]["total_price"], 20000000)
        self.assertEqual(rows[1]["trade_date"], "2026-10-24")
        self.assertEqual(rows[1]["parking_price"], 2000000)


class TestIngestDI(unittest.TestCase):
    def test_di_fetcher(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("a_lvr_land_a.csv", SAMPLE)
        zbytes = buf.getvalue()

        def fake_fetcher(_season: str) -> bytes:
            return zbytes

        rows = ingest_lvr(fake_fetcher, "115S1", ["a_lvr_land_a.csv"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["district"], "信義區")


class TestSecureContext(unittest.TestCase):
    """REQ:DEPLOY:TLS — plvr 憑證缺 SKI，只關閉 X509_STRICT 結構檢查；
    密碼學驗證（信任鏈/到期/hostname）必須完整保留。Red Evidence：
    任何把 verify_mode 改 CERT_NONE 或 check_hostname=False 的變異須讓本測試失敗。"""

    def test_verification_stays_on(self):
        ctx = build_secure_ssl_context()
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)

    def test_only_strict_flag_relaxed(self):
        ctx = build_secure_ssl_context()
        self.assertFalse(ctx.verify_flags & ssl.VERIFY_X509_STRICT)  # 結構檢查放寬
        # 其餘預設驗證旗標不得被一併清掉
        default = ssl.create_default_context().verify_flags
        self.assertTrue(ctx.verify_flags & (default & ~ssl.VERIFY_X509_STRICT))


if __name__ == "__main__":
    unittest.main()
