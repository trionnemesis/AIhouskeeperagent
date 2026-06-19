"""Public safety service — pure module, no fastmcp dependency.

追溯: spec-kit/05-data-mcp/public-safety-mcp.md (DI-5 治安粒度封頂)。
"""

from public_safety_mcp.guards import aggregate_density, assert_area_granularity

_SOURCE = "內政部警政署"


def traffic_accident_density(
    points: list[dict],
    lat: float,
    lng: float,
    radius_m: float,
    min_n: int = 1,
) -> dict:
    """交通事故密度 (聚合)。輸出不得含個別事故點座標。"""
    if not points:
        return {"outcome": "refused", "reason": "insufficient_data"}
    return {
        "outcome": "provided",
        "density": aggregate_density(points),
        "time_range": "近一年",
        "source": _SOURCE,
    }


def area_crime_stats(scope: dict, stats: list) -> dict:
    """區域治安統計 (鄉鎮市區層級)。粒度過細則拒絕。"""
    try:
        assert_area_granularity(scope)
    except ValueError:
        return {"outcome": "refused", "reason": "granularity_too_fine"}
    return {
        "outcome": "provided",
        "granularity": "鄉鎮市區",
        "stats": stats,
        "source": _SOURCE,
    }
