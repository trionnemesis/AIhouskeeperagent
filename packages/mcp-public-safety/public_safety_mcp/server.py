"""FastMCP 接線骨架 — 測試不 import 本檔 (fastmcp 未安裝)。"""

from fastmcp import FastMCP

from .service import area_crime_stats, traffic_accident_density

mcp = FastMCP("public-safety-mcp")


@mcp.tool()
def traffic_accident_density_tool(
    points: list[dict], lat: float, lng: float, radius_m: float, min_n: int = 1
) -> dict:
    return traffic_accident_density(points, lat, lng, radius_m, min_n)


@mcp.tool()
def area_crime_stats_tool(scope: dict, stats: list) -> dict:
    return area_crime_stats(scope, stats)
