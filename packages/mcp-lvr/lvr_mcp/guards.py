"""LVR 防護邏輯 — Inv-4（時間戳防護）。純模組，無 fastmcp 依賴。"""

from datetime import date, timedelta

_LOWER_BOUND = date(2010, 1, 1)
_UPPER_OFFSET = timedelta(days=90)


def timestamp_guard(rows: list[dict], today: str) -> list[dict]:
    """保留 '2010-01-01' <= trade_date <= (today + 90 天)；剔除超範圍與無法解析者（Inv-4）。"""
    # 上界隨 today 浮動以容忍預售/登記延遲，但仍封頂避免污染資料進入行情
    upper = date.fromisoformat(today) + _UPPER_OFFSET
    kept: list[dict] = []
    for row in rows:
        try:
            d = date.fromisoformat(row["trade_date"])
        except (ValueError, KeyError, TypeError):
            continue
        if _LOWER_BOUND <= d <= upper:
            kept.append(row)
    return kept


def net_unit_price(total: int, parking: int, area_ping: float) -> float | None:
    """(total - parking) / area_ping；area_ping <= 0 回 None。"""
    if area_ping <= 0:
        return None
    return (total - parking) / area_ping
