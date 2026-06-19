"""Public-safety 真實資料 ingest（data.gov.tw 犯罪資料，區域級）。parser 純函式；fetcher DI。
追溯: CR-2026-004。DI-5：僅區域級，輸出不含座標/門牌。
犯罪 CSV: type,oc_year(ROC),oc_data(MMDD),oc_county,oc_region + 中文標籤列。
"""
import csv
import io
from collections import Counter
from typing import Callable


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


def ingest_crime(fetcher: Callable[[str], str], url: str) -> list[dict]:
    """fetcher(url)→CSV text→parse。fetcher 注入(DI)。"""
    return parse_crime_csv(fetcher(url))


def live_fetch_crime(url: str) -> str:
    """deploy-time live fetcher：下載 data.gov.tw 犯罪 CSV。"""
    import urllib.request
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (官方來源)
        return resp.read().decode("utf-8-sig")
