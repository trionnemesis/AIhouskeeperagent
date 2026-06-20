"""FastMCP 接線 — 從 datastore 快取讀行情（真正部署）。測試不 import 本檔（fastmcp 未安裝）。

啟動：python scripts/serve.py lvr （launcher 設好 sys.path / DATA_MCP_DB）。
"""
import os

from fastmcp import FastMCP

from datastore import store
from lvr_mcp.service import query_market

mcp = FastMCP("lvr-mcp")

# DB 路徑由環境覆寫（部署），預設落在 repo var/。
_DB = os.environ.get("DATA_MCP_DB", "var/data_mcp.db")


@mcp.tool()
def query_market_tool(district: str, today: str, min_comps: int = 3) -> dict:
    """讀快取中該行政區 comps → 行情查詢（Inv-5 拒答優於猜測）。"""
    conn = store.connect(_DB)
    try:
        rows = store.query_lvr_comps(conn, district)
    finally:
        conn.close()
    return query_market(rows, today, min_comps)


if __name__ == "__main__":
    mcp.run()
