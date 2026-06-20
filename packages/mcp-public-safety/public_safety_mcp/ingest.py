"""Public-safety 真實資料 ingest（data.gov.tw 犯罪資料，區域級）。parser 純函式；fetcher DI。
追溯: CR-2026-004。DI-5：僅區域級，輸出不含座標/門牌。
犯罪 CSV: type,oc_year(ROC),oc_data(MMDD),oc_county,oc_region + 中文標籤列。
"""
import csv
import io
from collections import Counter
from datetime import date
from typing import Callable

from govnet.tls import build_secure_ssl_context, with_retry


def parse_crime_csv(text: str) -> list[dict]:
    """犯罪 CSV → rows（首列為 keys；第二列中文標籤跳過）。"""
    text = text.lstrip("﻿")
    reader = list(csv.reader(io.StringIO(text)))
    if len(reader) < 3:
        return []
    header = reader[0]
    return [dict(zip(header, r)) for r in reader[2:] if len(r) == len(header)]


def aggregate_crime(rows: list[dict], county: str, region: str) -> list[dict]:
    """依 (county, region) 篩選並按案類聚合計數（區域級，無座標，DI-5）。"""
    sel = [r for r in rows if r.get("oc_county") == county and r.get("oc_region") == region]
    counts = Counter(r.get("type", "") for r in sel)
    years = sorted({r.get("oc_year", "") for r in sel})
    period = "+".join(y for y in years if y)
    return [
        {"category": cat, "count": n, "period": period}
        for cat, n in sorted(counts.items())
    ]


def aggregate_crime_all(rows: list[dict]) -> list[dict]:
    """全行政區批次聚合：按 (oc_county, oc_region) 分組，各組按案類計數（DI-5 區域級）。

    供 ETL 一次落地整份 CSV 的所有鄉鎮市區（取代逐區呼叫 aggregate_crime）。
    """
    keys = sorted({(r.get("oc_county", ""), r.get("oc_region", "")) for r in rows})
    groups: list[dict] = []
    for county, region in keys:
        if not region:
            continue
        groups.append({"county": county, "region": region,
                       "stats": aggregate_crime(rows, county, region)})
    return groups


def parse_accidents_csv(text: str, severity: str) -> list[dict]:
    """NPA A1/A2 道路交通事故 CSV → 點位 rows。

    A1/A2 由 severity 參數帶入（NPA 多為 A1/A2 分檔）。欄位：發生年度(ROC)/月/日/經度/緯度。
    缺座標/無法解析者略過。注意 DI-5：點位僅入庫供「周邊密度聚合」，tool 不得回個別點。
    """
    text = text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    out: list[dict] = []
    for r in reader:
        lat, lng = _to_float(r.get("緯度")), _to_float(r.get("經度"))
        if lat is None or lng is None:
            continue
        iso = _roc_ymd_to_iso(r.get("發生年度"), r.get("發生月"), r.get("發生日"))
        out.append({"lat": lat, "lng": lng, "severity": severity, "occurred_at": iso})
    return out


def _to_float(s) -> float | None:
    try:
        v = float((s or "").strip())
    except (ValueError, AttributeError):
        return None
    return v if v != 0.0 else None  # 0/空座標視為無效


def _roc_ymd_to_iso(y, m, d) -> str | None:
    try:
        return date(int(y) + 1911, int(m), int(d)).isoformat()
    except (ValueError, TypeError):
        return None


def ingest_crime(fetcher: Callable[[str], str], url: str) -> list[dict]:
    """fetcher(url)→CSV text→parse。fetcher 注入(DI)。"""
    return parse_crime_csv(fetcher(url))


def live_fetch_crime(url: str) -> str:
    """deploy-time live fetcher：下載犯罪/事故 CSV。

    opdadm.moi.gov.tw 與 plvr 同樣憑證缺 SKI → 走 govnet.build_secure_ssl_context（驗證仍開）；
    政府 WAF 擋預設 UA → 帶瀏覽器 UA；暫態錯誤有界重試。
    """
    import urllib.request
    ctx = build_secure_ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    def _fetch() -> str:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:  # noqa: S310 (官方來源)
            return resp.read().decode("utf-8-sig")

    return with_retry(_fetch, retries=3, backoff_base=2.0)
