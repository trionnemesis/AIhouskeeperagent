# language: zh-TW
@p0 @gateB @governance
功能: 租戶隔離（Tenant Isolation, Inv-1）
  作為 平台
  我要 確保所有業務資料存取都硬約束於正確租戶
  以便 避免跨客戶 PII 外洩（H1：session_key 非租戶邊界）

  背景:
    假設 存在租戶 "信義加盟A店" 與其經紀人 "seat-A1"
    而且 存在租戶 "永慶直營B店" 與其經紀人 "seat-B1"
    而且 "seat-A1" 名下有客戶 "林先生"
    而且 "seat-B1" 名下有客戶 "陳小姐"

  場景: 解析不到 scope 的請求一律拒絕
    當 一個 LINE userId 沒有綁定任何 seat 發來訊息
    那麼 系統 應 拒絕處理（不產生任何對話回覆）
    而且 應發出事件 "UnauthorizedAccessBlocked"
    # action=unauthorized_no_scope
    而且 應發出事件 "AuditTrailRecorded"

  場景: 查詢自動注入 tenant scope
    假設 目前 scope 為 tenant="信義加盟A店", seat="seat-A1"
    當 "seat-A1" 查詢自己的客戶清單
    那麼 結果只包含 "林先生"
    而且 結果 不應 包含 "陳小姐"

  場景: 跨租戶查詢回傳空集合並告警
    假設 目前 scope 為 tenant="信義加盟A店", seat="seat-A1"
    當 系統嘗試以 "陳小姐" 的 customer_id 直接查詢（跨租戶）
    那麼 查詢結果為空
    而且 應發出事件 "TenantScopeViolationDetected"
    # append-only
    而且 應發出事件 "AuditTrailRecorded"

  場景: 缺少 tenant_id 的資料存取被拒
    當 任何資料存取未帶 tenant_id 進入存取層
    那麼 該存取 應 被拒絕執行
    而且 不應 退化為「查全部」

  @core
  場景: 配對不可跨租戶（Inv-1 套用於 C6）
    假設 "永慶直營B店" 有一筆符合 "林先生" 需求的物件
    當 為 "林先生"（屬信義加盟A店）執行配對
    那麼 配對候選 不應 包含任何屬於 "永慶直營B店" 的物件
