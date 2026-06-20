"""govnet 共用基建測試（REQ:DEPLOY:TLS / REQ:DEPLOY:RETRY）。"""
import ssl
import unittest

from govnet.tls import build_secure_ssl_context, with_retry


class TestSecureContext(unittest.TestCase):
    """政府源憑證缺 SKI，只關閉 X509_STRICT 結構檢查；密碼學驗證必須完整保留。
    Red Evidence：把 verify_mode 改 CERT_NONE 或 check_hostname=False 須讓本測試失敗。"""

    def test_verification_stays_on(self):
        ctx = build_secure_ssl_context()
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)

    def test_only_strict_flag_relaxed(self):
        ctx = build_secure_ssl_context()
        self.assertFalse(ctx.verify_flags & ssl.VERIFY_X509_STRICT)  # 結構檢查放寬
        default = ssl.create_default_context().verify_flags  # 其餘預設旗標不得被一併清掉
        self.assertTrue(ctx.verify_flags & (default & ~ssl.VERIFY_X509_STRICT))


class TestWithRetry(unittest.TestCase):
    """有界重試 + backoff（sleeper 注入，deterministic）。斷路器不在此（Gateway Router）。"""

    def test_succeeds_after_transient_failures(self):
        calls = {"n": 0}
        slept = []

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise OSError("transient")
            return b"ok"

        out = with_retry(flaky, retries=3, backoff_base=0.5, sleeper=slept.append)
        self.assertEqual(out, b"ok")
        self.assertEqual(calls["n"], 3)
        self.assertEqual(slept, [0.5, 1.0])  # 指數退避，2 次失敗→睡 2 次

    def test_gives_up_after_max_retries(self):
        def always_fail():
            raise OSError("down")

        with self.assertRaises(OSError):
            with_retry(always_fail, retries=2, backoff_base=0.1, sleeper=lambda _s: None)

    def test_no_sleep_on_first_success(self):
        slept = []
        out = with_retry(lambda: b"x", retries=3, backoff_base=1.0, sleeper=slept.append)
        self.assertEqual(out, b"x")
        self.assertEqual(slept, [])


if __name__ == "__main__":
    unittest.main()
