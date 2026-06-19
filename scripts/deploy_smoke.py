"""GATE:DEPLOY smoke test — 以 FastMCP in-memory Client 啟動 server.py 並實呼工具。
執行：.venv/bin/python scripts/deploy_smoke.py
追溯：spec-kit/05-data-mcp/changes/CR-2026-001/gates.md、07 治理 GATE:DEPLOY(smoke_test_present)。
"""
import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages" / "mcp-lvr"))
sys.path.insert(0, str(ROOT / "packages" / "mcp-public-safety"))

from fastmcp import Client  # noqa: E402
import lvr_mcp.server as lvr_srv  # noqa: E402
import public_safety_mcp.server as ps_srv  # noqa: E402

VALID_ROWS = [
    {"trade_date": "2026-01-15", "total_price": 20000000, "district": "信義區"},
    {"trade_date": "2026-02-10", "total_price": 18000000, "district": "信義區"},
    {"trade_date": "2026-03-05", "total_price": 22000000, "district": "信義區"},
]


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
    await smoke("lvr-mcp", lvr_srv.mcp, [
        ("query_market_tool", {"rows": VALID_ROWS, "today": "2026-06-20"},
         lambda d: d.get("outcome") == "provided" and d.get("n") == 3, "3 有效 comps→provided"),
    ])
    await smoke("public-safety-mcp", ps_srv.mcp, [
        ("area_crime_stats_tool", {"scope": {"district": "信義區"}, "stats": [{"category": "竊盜", "count": 5}]},
         lambda d: d.get("outcome") == "provided" and d.get("granularity") == "鄉鎮市區", "區域級→provided"),
        ("area_crime_stats_tool", {"scope": {"address": "信義路五段7號"}, "stats": []},
         lambda d: d.get("outcome") == "refused", "門牌級→refused(DI-5)"),
        ("traffic_accident_density_tool", {"points": [{"severity": "A2"}], "lat": 25.0, "lng": 121.5, "radius_m": 500},
         lambda d: d.get("outcome") == "provided" and "lat" not in str(d.get("density")), "聚合→無座標(DI-5)"),
    ])
    print("\n✅ GATE:DEPLOY smoke 通過：兩 server 可啟動、工具可呼叫且行為符 spec（含 DI-5 拒答）。")


if __name__ == "__main__":
    asyncio.run(main())
