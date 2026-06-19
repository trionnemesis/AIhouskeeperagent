"""LVR 行情查詢服務 — Inv-5（拒答優於猜測）。純模組，無 fastmcp 依賴。"""

from lvr_mcp.guards import timestamp_guard

_SOURCE = "內政部不動產交易實價查詢服務網"


def query_market(rows: list[dict], today: str, min_comps: int = 3) -> dict:
    """guarded 數量不足 min_comps → refused（Inv-5）；否則 provided。"""
    guarded = timestamp_guard(rows, today)
    if len(guarded) < min_comps:
        return {"outcome": "refused", "reason": "insufficient_comps"}
    return {
        "outcome": "provided",
        "comps": guarded,
        "n": len(guarded),
        "data_as_of": today[:7],
        "source": _SOURCE,
    }
