# language: zh-TW
# STDD×VDD：須先過 GATE:RED；斷言業務結果；含負向/邊界。對應 CR-2026-002。
@data @gateway @router
功能: AI Gateway Router（來源路由 / 多源 fallback / 斷路器）
  作為 平台
  我要 在 Gateway 統一路由與降級
  以便 來源失效不崩、且永不降到禁用源

  規則: 來源路由（REQ:GW:ROUTER:001）

    場景: 已知 tool 導向正確 MCP server
      當 agent 呼叫 query_market
      那麼 Router 應 依路由表導向 lvr-mcp

    場景: 未知 tool 被拒
      當 agent 呼叫不在路由表的 tool
      那麼 應回傳錯誤碼 "SCOPE_NOT_ALLOWLISTED"

  規則: 多源 fallback 依 authority 階層（REQ:GW:ROUTER:002）

    場景: 主源失效退備源
      假設 geocoding 主源 TGOS 失效
      當 agent 請求 geocode
      那麼 Router 應 退到備源 NLSC
      而且 結果 應 標來源為實際使用的備源

    場景: 全源失效則降級不崩（REL-4）
      假設 某資料的所有官方源皆失效
      當 agent 查詢
      那麼 結果 outcome 應 為 "refused"，reason="source_unavailable"
      而且 系統 不應 崩潰

    場景: 永不 fallback 到禁用源
      假設 行情官方源失效
      當 Router 尋找備源
      那麼 不應 退到 591 或 leju（DI-4 黑名單）
      而且 寧可 refused 也不使用禁用源

  規則: 斷路器（REQ:GW:ROUTER:003）

    場景: 連續失敗觸發斷路
      假設 某來源連續失敗達閾值
      當 再次呼叫該來源
      那麼 Router 應 直接走降級（不打該來源）
      而且 冷卻後 應 半開重試
