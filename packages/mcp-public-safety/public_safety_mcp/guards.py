"""Public safety guards — pure module, no fastmcp dependency.

追溯: spec-kit/05-data-mcp/public-safety-mcp.md (DI-5 治安粒度封頂)。
"""


# DI-5: 過細粒度欄位 — 出現即拒絕，避免門牌/點位/單一物件揭露
_TOO_FINE_KEYS = ("address", "parcel", "listing_id")

_NEGATIVE_LABELS = ("高犯罪", "治安差", "嫌惡", "治安不好")


def aggregate_density(points: list[dict]) -> dict:
    """聚合事故/治安點為密度統計，回傳不得含個別點座標/地址 (DI-5: 僅聚合)。"""
    severity_mix: dict[str, int] = {}
    for point in points:
        sev = point["severity"]
        severity_mix[sev] = severity_mix.get(sev, 0) + 1
    return {"total_n": len(points), "severity_mix": severity_mix}


def contains_negative_label(text: str) -> bool:
    """偵測嫌惡性標籤字眼。"""
    return any(label in text for label in _NEGATIVE_LABELS)


def assert_area_granularity(scope: dict) -> None:
    """粒度封頂: 含 address/parcel/listing_id 即過細，僅 district 允許 (DI-5)。"""
    if any(key in scope for key in _TOO_FINE_KEYS):
        raise ValueError("GRANULARITY_TOO_FINE")
