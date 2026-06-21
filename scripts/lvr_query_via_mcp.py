"""透過 hermes-lvr MCP (stdio, .mcp.json 同設定) 取某行政區行情 comps，輸出 JSON。
用法: .venv/bin/python scripts/lvr_query_via_mcp.py 松山區 2026-06-21
僅供本地測試/workflow agent 取真實資料（資料來源=plvr 官方）。"""
import asyncio, json, sys, pathlib
from fastmcp import Client

REPO = pathlib.Path(__file__).resolve().parent.parent
district = sys.argv[1] if len(sys.argv) > 1 else "松山區"
today = sys.argv[2] if len(sys.argv) > 2 else "2026-06-21"

async def main():
    cfg = json.loads((REPO / ".mcp.json").read_text())["mcpServers"]["hermes-lvr"]
    async with Client({"mcpServers": {"hermes-lvr": cfg}}) as c:
        tools = await c.list_tools()
        qm = next(t.name for t in tools if t.name.endswith("query_market_tool"))
        res = await c.call_tool(qm, {"district": district, "today": today})
        data = res.data if getattr(res, "data", None) is not None else res.structured_content
        print(json.dumps(data, ensure_ascii=False))

asyncio.run(main())
