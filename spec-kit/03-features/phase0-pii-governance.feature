# language: zh-TW
@p0 @gateB @governance
功能: PII 治理（PII Governance, Inv-2/3/8）
  作為 平台
  我要 在最小揭露原則下處理客戶個資
  以便 符合個資法並建立法律免責證據鏈

  場景: PII 欄位在日誌與 prompt 中預設脫敏（Inv-8）
    假設 客戶 "林先生" 的電話為 "0912-345-678"
    當 系統將客戶脈絡寫入日誌或送入 LLM prompt
    那麼 電話 應 以脫敏遮罩呈現（如 "0912-***-678"）
    而且 原值 不應 出現在日誌或外送內容

  場景: MVP 治理最小集——不存真 PII，用代號
    當 在 Gate B 尚未完成完整治理層時建立客戶
    那麼 系統 應 以代號/脫敏值儲存敏感欄位
    而且 不應 落地身分證等高敏感原值

  場景: 含 PII 的建檔必經 HITL（Inv-2）
    假設 從語音擷取到含個資的客戶需求草稿
    當 系統準備建檔
    那麼 系統 應 先建立一筆 risk_level="high" 的 HITL 待核准
    而且 在核准前 不應 寫入客戶資料

  場景: 存取 PII 產生稽核（Inv-3）
    當 經紀人在 scope 內存取客戶的 PII 欄位
    那麼 應發出事件 "PiiAccessLogged"（含 field、purpose、by）
    而且 應發出事件 "AuditTrailRecorded"
      """
      envelope: tenant_id, seat_id, correlation_id, audit_ref
      payload : actor_type(human|agent|system), action, scope, payload_hash, pii_accessed=true
      """
    而且 該稽核為 append-only
    # 註：此場景定義 AuditTrailRecorded 完整結構；其餘 feature 以事件名引用即可

  場景: 稽核不可竄改（Inv-3）
    假設 已存在一筆稽核記錄
    當 任何角色嘗試 UPDATE 或 DELETE 該稽核
    那麼 操作 應 失敗（DB role 未授予寫改權限）

  規則: 被遺忘權與保留政策（Inv-10）

    場景: 客戶請求刪除經 HITL 核准後執行
      假設 客戶 "林先生" 已建檔且有 mem0 記憶
      當 經紀人發起刪除請求
      那麼 應發出事件 "CustomerErasureRequested"
      而且 應建立 risk_level="high" 的 HITL 待核准
      當 經紀人核准刪除
      那麼 應發出事件 "CustomerErasureApproved"
      而且 應呼叫 mem0 forget() 清除其 namespace
      而且 "林先生" 的 PII 欄位 應 被清空（status=erased、deleted_at 設定）
      而且 應發出事件 "CustomerErasureCompleted"
      而且 後續查詢 "林先生" 個資 應 查無資料

    場景: HITL 駁回刪除則中止（PII 不清除）
      假設 客戶 "林先生" 已發起刪除且有 high HITL 待核准
      當 經紀人駁回刪除
      那麼 應發出事件 "CustomerErasureRefused"
      而且 "林先生" 的 PII 欄位 應 維持不變
      而且 不應 呼叫 mem0 forget()

    場景: 刪除後稽核仍存但匿名化（Inv-3 與 Inv-10 並存）
      假設 "林先生" 已被刪除
      那麼 既有 audit_logs 記錄 應 仍存在（append-only 不刪）
      而且 該稽核 應 已脫去關聯 PII（僅留 payload_hash 與匿名 scope）
