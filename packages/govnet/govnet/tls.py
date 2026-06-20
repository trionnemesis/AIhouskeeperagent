"""政府 TLS 安全 context + 有界重試（共用基建）。

追溯: spec-kit/05-data-mcp/changes/CR-2026-005（TLS/retry 首版）、CR-2026-006（抽共用）。
"""
import ssl
import time
from typing import Callable


def build_secure_ssl_context() -> ssl.SSLContext:
    """政府源（*.moi.gov.tw）安全 TLS context。

    Why：plvr.land.moi.gov.tw / opdadm.moi.gov.tw 憑證鏈缺 Subject Key Identifier
    （RFC5280 結構不符），OpenSSL 3.x 預設開啟的 VERIFY_X509_STRICT 會以此拒絕。
    實測 certifi/補 CA 皆無效（非信任根缺失），唯一安全修法是**僅關閉 X509_STRICT
    結構檢查**。信任鏈、簽章、到期、hostname 驗證全部保留（CERT_REQUIRED + check_hostname）。
    **禁止** 改 CERT_NONE 或 check_hostname=False——那會讓 MITM 可偽冒這些端點。
    """
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def with_retry(fn: Callable, *, retries: int = 3, backoff_base: float = 1.0,
               sleeper: Callable[[float], None] = time.sleep):
    """有界重試 + 指數退避（暫態網路錯）。sleeper 注入(DI)以利測試。

    斷路器（連續失敗暫斷源）**不在此**——屬 Gateway Router REQ:GW:ROUTER:003，
    待 Gateway runtime 落地後上移，避免在 ETL 層臆造跨呼叫狀態。
    """
    attempt = 0
    while True:
        try:
            return fn()
        except Exception:
            if attempt >= retries:
                raise
            sleeper(backoff_base * (2 ** attempt))
            attempt += 1
