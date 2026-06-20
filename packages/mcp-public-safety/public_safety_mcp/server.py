"""FastMCP 接線 — area_crime_stats 從 datastore 快取讀（真正部署）。測試不 import 本檔。

啟動：python scripts/serve.py public-safety。
traffic_accident_density 維持 args（A1/A2 點位資料尚未 ingest，見 CR-2026-004 範圍外）。
"""
import os

from fastmcp import FastMCP

from datastore import store

from .service import area_crime_stats, traffic_accident_density

mcp = FastMCP("public-safety-mcp")

_DB = os.environ.get("DATA_MCP_DB", "var/data_mcp.db")


@mcp.tool()
def traffic_accident_density_tool(
    lat: float, lng: float, radius_m: float, min_n: int = 1
) -> dict:
    """讀快取半徑內事故點 → 聚合密度（DI-5：僅回密度，不回個別點）。"""
    conn = store.connect(_DB)
    try:
        points = store.query_accident_points_near(conn, lat, lng, radius_m)
    finally:
        conn.close()
    return traffic_accident_density(points, lat, lng, radius_m, min_n)


@mcp.tool()
def area_crime_stats_tool(scope: dict) -> dict:
    """粒度過細（門牌/地號）先拒（DI-5）；否則讀快取該鄉鎮市區統計。"""
    district = scope.get("district")
    stats: list = []
    if district:
        conn = store.connect(_DB)
        try:
            stats = store.query_crime_stats(conn, district)
        finally:
            conn.close()
    return area_crime_stats(scope, stats)


if __name__ == "__main__":
    mcp.run()
