"""ETL 排程純函式（REQ:DEPLOY:SCHED）。

plvr 實價登錄每旬發布（每月 1/11/21）。本模組僅含 deterministic 計算，
排程觸發（cron）與 I/O 落地在 scripts/etl_run.py。
追溯: spec-kit/05-data-mcp/changes/CR-2026-005-deploy-hardening/
"""
from datetime import date

# plvr 每旬發布日（內政部不動產交易實價查詢服務網）
PUBLICATION_DAYS = (1, 11, 21)


def next_publication_date(after: date) -> date:
    """plvr 下一個發布日（嚴格大於 after）。供排程計算與監控用。"""
    for d in PUBLICATION_DAYS:
        if d > after.day:
            return date(after.year, after.month, d)
    # 本月發布日已過 → 跨月，回次月第一個發布日
    year, month = (after.year + 1, 1) if after.month == 12 else (after.year, after.month + 1)
    return date(year, month, PUBLICATION_DAYS[0])


def is_stale(data_as_of: date, today: date, max_age_days: int) -> bool:
    """資料新鮮度監控（DI-9 短 TTL）：資料齡 > max_age_days → stale，應觸發重抓。"""
    return (today - data_as_of).days > max_age_days


def season_for(d: date) -> str:
    """日期 → plvr 季別字串（民國年 + 季）。如 2026-06 → '115S2'。

    注意：實登申報遲延 3–5 月，ETL 實抓時應同時抓「上一季」校正（DI-9），見 etl_run.py。
    """
    roc_year = d.year - 1911
    quarter = (d.month - 1) // 3 + 1
    return f"{roc_year}S{quarter}"
