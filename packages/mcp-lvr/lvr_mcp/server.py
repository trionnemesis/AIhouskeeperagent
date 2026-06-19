"""FastMCP 接線骨架。測試不 import 本檔（fastmcp 未安裝）。"""

from fastmcp import FastMCP

from lvr_mcp.service import query_market

mcp = FastMCP("lvr-mcp")


@mcp.tool()
def query_market_tool(rows: list[dict], today: str, min_comps: int = 3) -> dict:
    return query_market(rows, today, min_comps)


if __name__ == "__main__":
    mcp.run()
