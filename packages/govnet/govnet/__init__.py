"""政府開放資料網路存取共用基建（TLS 安全 context + 有界重試）。

Why 抽成共用：plvr.land.moi.gov.tw 與 opdadm.moi.gov.tw（內政部多個源）皆有相同
憑證鏈缺 Subject Key Identifier 的問題，需同一安全修法。安全紅線只能有一處實作。
"""
from govnet.tls import build_secure_ssl_context, with_retry  # noqa: F401
