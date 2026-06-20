"""ETL 落地 runner（REQ:DEPLOY:STORE/SCHED 的 I/O 邊界）。

組合純核心：schedule.season_for + ingest 解析 + datastore 落地。
排程（部署）：cron `0 6 1,11,21 * *`（每旬發布日 06:00 跑），見 deployment 文件。

用法：
  python scripts/etl_run.py lvr  --county A_lvr_land_a.csv --season 115S2
  python scripts/etl_run.py crime --url https://...csv --county 新竹縣 --region 湖口鄉
不帶 --season 時，依今日推算「本季 + 上一季」（DI-9 校正）。
"""
import argparse
import datetime
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in ("packages/govnet", "packages/datastore", "packages/mcp-lvr", "packages/mcp-public-safety"):
    sys.path.insert(0, str(ROOT / p))

from datastore import store  # noqa: E402
from lvr_mcp import ingest as lvr_ingest  # noqa: E402
from lvr_mcp import schedule  # noqa: E402
from public_safety_mcp import ingest as ps_ingest  # noqa: E402

_SQM_PER_PING = 3.305785
_LVR_SOURCE = "內政部不動產交易實價查詢服務網"
_CRIME_SOURCE = "內政部警政署"


def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _to_erd_row(r: dict) -> dict:
    """parse_lvr_csv 輸出 → erd lvr_trades 欄位（含重算淨單價、坪換算）。"""
    area_ping = round(r["area_sqm"] / _SQM_PER_PING, 2) if r.get("area_sqm") else 0.0
    net = lvr_ingest_net(r["total_price"], r.get("parking_price", 0), area_ping)
    return {
        "district": r["district"],
        "deal_type": "rent" if "租" in r.get("deal_target", "") else "sale",
        "building_type": "預售" if "預售" in r.get("deal_target", "") else "成屋",
        "trade_date": r["trade_date"],
        "total_price": r["total_price"],
        "unit_price_net": net,
        "area_ping": area_ping,
        "parking_price": r.get("parking_price", 0),
        "project_name": None,
    }


def lvr_ingest_net(total: int, parking: int, area_ping: float):
    from lvr_mcp.guards import net_unit_price
    return net_unit_price(total, parking, area_ping)


def run_lvr(db: str, counties: list[str], seasons: list[str]) -> int:
    today = datetime.date.today()
    if not seasons:
        prev = today - datetime.timedelta(days=95)  # 上一季校正（申報遲延）
        seasons = sorted({schedule.season_for(today), schedule.season_for(prev)})
    conn = store.connect(db)
    store.init_schema(conn)
    total = 0
    for season in seasons:
        raw = lvr_ingest.ingest_lvr(lvr_ingest.live_fetch_plvr, season, counties)
        erd_rows = [_to_erd_row(r) for r in raw]
        added = store.upsert_lvr_trades(conn, erd_rows, source=_LVR_SOURCE,
                                        data_as_of=season, ingested_at=_now_iso())
        print(f"[lvr] season={season} parsed={len(raw)} added={added}")
        total += added
    conn.close()
    return total


def run_crime(db: str, url: str, county: str | None, region: str | None) -> int:
    rows = ps_ingest.ingest_crime(ps_ingest.live_fetch_crime, url)
    conn = store.connect(db)
    store.init_schema(conn)
    as_of = str(datetime.date.today().year)
    total = 0
    if region:  # 單一行政區
        stats = ps_ingest.aggregate_crime(rows, county, region)
        total = store.upsert_crime_area_stats(conn, region, stats, source=_CRIME_SOURCE,
                                              as_of=as_of, ingested_at=_now_iso())
        print(f"[crime] {county}{region} categories={len(stats)} added={total}")
    else:  # 全行政區批次（DI-5 區域級）
        for g in ps_ingest.aggregate_crime_all(rows):
            total += store.upsert_crime_area_stats(conn, g["region"], g["stats"], source=_CRIME_SOURCE,
                                                   as_of=as_of, ingested_at=_now_iso())
        print(f"[crime] 全行政區批次 groups={len(ps_ingest.aggregate_crime_all(rows))} added={total}")
    conn.close()
    return total


def run_traffic(db: str, url: str, severity: str) -> int:
    raw = ps_ingest.live_fetch_crime(url)  # 同為 data.gov.tw CSV（共用 UA fetcher）
    rows = ps_ingest.parse_accidents_csv(raw, severity)
    conn = store.connect(db)
    store.init_schema(conn)
    added = store.upsert_traffic_accidents(conn, rows, source=_CRIME_SOURCE,
                                           as_of=str(datetime.date.today().year), ingested_at=_now_iso())
    conn.close()
    print(f"[traffic] severity={severity} points={len(rows)} added={added}")
    return added


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap_lvr = sub.add_parser("lvr")
    ap_lvr.add_argument("--db", default=str(ROOT / "var" / "data_mcp.db"))
    ap_lvr.add_argument("--county", action="append", required=True, help="ZIP 內檔名，可多次")
    ap_lvr.add_argument("--season", action="append", default=[], help="如 115S2，可多次；省略則本季+上季")
    ap_c = sub.add_parser("crime")
    ap_c.add_argument("--db", default=str(ROOT / "var" / "data_mcp.db"))
    ap_c.add_argument("--url", required=True)
    ap_c.add_argument("--county", help="省略 county+region 則全行政區批次落地")
    ap_c.add_argument("--region", help="省略則全行政區批次")
    ap_t = sub.add_parser("traffic")
    ap_t.add_argument("--db", default=str(ROOT / "var" / "data_mcp.db"))
    ap_t.add_argument("--url", required=True)
    ap_t.add_argument("--severity", required=True, choices=["A1", "A2"])
    args = ap.parse_args()
    if args.cmd == "lvr":
        run_lvr(args.db, args.county, args.season)
    elif args.cmd == "crime":
        run_crime(args.db, args.url, args.county, args.region)
    else:
        run_traffic(args.db, args.url, args.severity)


if __name__ == "__main__":
    main()
