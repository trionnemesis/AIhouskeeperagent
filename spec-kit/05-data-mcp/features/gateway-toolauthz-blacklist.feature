# language: zh-TW
@data @gateway @toolauthz @gateB
功能: 來源黑名單與授權（ToolAuthZ · DI-4）
  作為 平台
  我要 在 ToolAuthZ 禁用 591/leju 等高風險來源
  以便 避免公平會裁罰先例與刑事風險（R3）

  背景:
    假設 591 與 leju 在 source_blacklist，allowlisted=false
    而且 黑名單依據：公平會公處字第106084號、刑法§358/§359、各站 ToS

  場景: 預設禁用 591/leju 來源工具
    當 agent 嘗試呼叫以 591 或 leju 為來源的工具
    那麼 ToolAuthZ 應 拒絕
    而且 應發出事件 "AuditTrailRecorded"
    而且 robots.txt 是否允許 不應 作為放行依據

  場景: 僅法務簽核 + 授權證明才放行
    假設 已取得法務意見書與 591 B2B 授權證明
    當 管理者於 Gateway 設定該來源 allowlisted=true
    那麼 該來源工具 才 可被授權角色呼叫

  場景: 出向層雙重封鎖
    當 任一程式嘗試直連 591/leju 網域
    那麼 出向層 應 封鎖該網域（與 ToolAuthZ 黑名單雙重保險）

  場景: 角色 × 工具授權
    假設 agent 角色無權呼叫某 tool
    當 嘗試呼叫
    那麼 應回傳錯誤碼 "SCOPE_NOT_ALLOWLISTED"

  場景: 來源配額超限（DI-8，外部源每日上限≠並發）
    當 對 GCIS 的呼叫超出每日次數上限
    那麼 應回傳錯誤碼 "SOURCE_QUOTA_EXCEEDED"
