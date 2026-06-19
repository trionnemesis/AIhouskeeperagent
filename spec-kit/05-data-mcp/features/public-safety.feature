# language: zh-TW
# STDD×VDD：每個場景對應 REQ:PUBSAFE:*，須先過 GATE:RED（baseline 失敗 + Red Evidence），
# 斷言業務結果(非僅 status)，含負向/邊界/粒度。實作 Agent 不得弱化（GATE:GREEN protected_tests）。
@data @public-safety @p2
功能: 治安/防詐資料（public-safety-mcp · DI-5 粒度封頂）
  作為 房仲 agent
  我要 提供物件「周邊安全」資訊
  以便 回答客戶又不造假、不汙名化（DI-5）

  背景:
    假設 public-safety-mcp 僅用警政署/165 官方 open data（不爬 ba.npa.gov.tw、不消費第三方 hosted MCP）

  規則: 交通事故以周邊密度聚合（REQ:PUBSAFE:001, DI-5）

    場景: 提供周邊事故密度並附時點與顯名
      當 agent 查詢某座標周邊交通事故
      那麼 結果 outcome 應 為 "provided"
      而且 應 以「周邊密度聚合」呈現，不回個別事故點
      而且 應 附 time_range 與來源「內政部警政署」
      而且 應發出事件 "AuditTrailRecorded"

    場景: A1/A2 點位不外洩為門牌級精準
      當 agent 查詢周邊交通事故
      那麼 輸出 不應 含門牌或單點精準座標
      而且 僅輸出聚合密度（DI-5）

    場景: 資料不足即拒答
      當 某座標周邊事故樣本不足
      那麼 結果 outcome 應 為 "refused"，reason="insufficient_data"

  規則: 區域治安統計止於鄉鎮市區（REQ:PUBSAFE:002, DI-5）

    場景: 提供區域統計並標粒度
      當 agent 查詢某行政區治安統計
      那麼 結果 outcome 應 為 "provided"
      而且 應 標 granularity="鄉鎮市區" 與資料期間
      而且 應發出事件 "AuditTrailRecorded"

    場景: 禁將區域統計套到單一物件
      當 agent 嘗試取得單一物件的精準治安評分
      那麼 系統 不應 回傳物件級治安評分
      而且 應 改回行政區級統計並標粒度

    場景: 禁對物件貼負面標籤
      當 產生周邊治安說明
      那麼 輸出 不應 含「高犯罪/治安差/嫌惡」等對物件的負面標籤
      # Policy 插件攔截（gateway-compliance.md）

    場景: 來源不可用時降級（REL-4）
      假設 警政署 open data 來源不可用
      當 agent 查詢區域治安統計
      那麼 結果 outcome 應 為 "refused"，reason="source_unavailable"
      而且 系統 不應 崩潰

    場景: 來源配額超限（DI-8）
      當 對資料來源呼叫超出每日配額
      那麼 應回傳錯誤碼 "SOURCE_QUOTA_EXCEEDED"

  規則: 防詐查核（REQ:PUBSAFE:003, P3）

    場景: 涉詐網站命中
      假設 165 清單含某網域
      當 agent 以該網域查詢防詐
      那麼 結果 outcome 應 為 "provided"
      而且 應 標來源「165」與 as_of
