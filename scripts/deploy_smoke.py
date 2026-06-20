"""GATE:DEPLOY smoke — 以 FastMCP in-memory Client 啟動 server.py 並實呼工具。
seed datastore 快取 → cache-backed 工具讀取（真正部署形態）。
執行：.venv/bin/python scripts/deploy_smoke.py
追溯：changes/CR-2026-005-deploy-hardening/、CR-2026-001/gates.md、07 治理 GATE:DEPLOY。
"""
import asyncio
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in ("packages/govnet", "packages/datastore", "packages/mcp-lvr", "packages/mcp-public-safety"):
    sys.path.insert(0, str(ROOT / p))

# 用臨時 db，import server 前設好環境（server 於 import 時讀 DATA_MCP_DB 預設）
_TMP_DB = str(pathlib.Path(tempfile.mkdtemp()) / "smoke.db")
os.environ["DATA_MCP_DB"] = _TMP_DB

from datastore import store  # noqa: E402
from fastmcp import Client  # noqa: E402
import lvr_mcp.server as lvr_srv  # noqa: E402
import public_safety_mcp.server as ps_srv  # noqa: E402

_TS = "2026-06-20T06:00:00+08:00"


def seed():
    conn = store.connect(_TMP_DB)
    store.init_schema(conn)
    store.upsert_lvr_trades(conn, [
        {"district": "信義區", "trade_date": "2026-01-15", "total_price": 20000000,
         "area_ping": 30.0, "unit_price_net": 666666.0, "parking_price": 0,
         "building_type": "成屋", "deal_type": "sale"},
        {"district": "信義區", "trade_date": "2026-02-10", "total_price": 18000000,
         "area_ping": 25.0, "unit_price_net": 720000.0, "parking_price": 0,
         "building_type": "成屋", "deal_type": "sale"},
        {"district": "信義區", "trade_date": "2026-03-05", "total_price": 22000000,
         "area_ping": 33.0, "unit_price_net": 666666.0, "parking_price": 0,
         "building_type": "成屋", "deal_type": "sale"},
    ], source="內政部不動產交易實價查詢服務網", data_as_of="2026S1", ingested_at=_TS)
    store.upsert_crime_area_stats(conn, "信義區",
                                  [{"category": "竊盜", "count": 5, "period": "115"}],
                                  source="內政部警政署", as_of="2026", ingested_at=_TS)
    store.upsert_traffic_accidents(conn, [
        {"lat": 25.000, "lng": 121.500, "severity": "A1", "occurred_at": "2026-07-01"},
        {"lat": 25.003, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-02"},
        {"lat": 25.050, "lng": 121.500, "severity": "A2", "occurred_at": "2026-07-03"},  # ~5.5km 外
    ], source="內政部警政署", as_of="2026", ingested_at=_TS)
    conn.close()


def _data(res):
    return res.data if getattr(res, "data", None) is not None else res.structured_content


async def smoke(name, mcp, calls):
    async with Client(mcp) as c:
        await c.ping()
        tools = [t.name for t in await c.list_tools()]
        print(f"[{name}] reachable; tools={tools}")
        for tool, args, check, desc in calls:
            data = _data(await c.call_tool(tool, args))
            ok = check(data)
            print(f"  {tool} ({desc}) → outcome={data.get('outcome')} PASS={ok}")
            assert ok, f"smoke FAILED: {tool} → {data}"


async def main():
    seed()
    await smoke("lvr-mcp", lvr_srv.mcp, [
        ("query_market_tool", {"district": "信義區", "today": "2026-06-20"},
         lambda d: d.get("outcome") == "provided" and d.get("n") == 3, "快取 3 comps→provided"),
        ("query_market_tool", {"district": "大安區", "today": "2026-06-20"},
         lambda d: d.get("outcome") == "refused", "無快取→refused(Inv-5)"),
    ])
    await smoke("public-safety-mcp", ps_srv.mcp, [
        ("area_crime_stats_tool", {"scope": {"district": "信義區"}},
         lambda d: d.get("outcome") == "provided" and d.get("granularity") == "鄉鎮市區"
         and len(d.get("stats", [])) == 1, "快取區域級→provided"),
        ("area_crime_stats_tool", {"scope": {"address": "信義路五段7號"}},
         lambda d: d.get("outcome") == "refused", "門牌級→refused(DI-5)"),
        ("traffic_accident_density_tool", {"lat": 25.0, "lng": 121.5, "radius_m": 500},
         lambda d: d.get("outcome") == "provided" and d.get("density", {}).get("total_n") == 2
         and "lat" not in str(d.get("density")), "快取半徑內 2 點聚合→無座標(DI-5)"),
    ])
    print("\n✅ GATE:DEPLOY smoke 通過：兩 server 可啟動、cache-backed 工具可呼叫且行為符 spec（含 Inv-5 / DI-5 拒答）。")


if __name__ == "__main__":
    asyncio.run(main())
