# language: zh-TW
@p2 @core
功能: 結構化客戶記憶（Customer Memory · 護城河核心）
  作為 經紀人
  我要 用 LINE 語音/訊息把客戶需求結構化建檔並主動被提醒
  以便 形成切換成本與留存（真護城河，非行情）

  背景:
    假設 目前 scope 為 tenant="信義加盟A店", seat="seat-A1"

  場景: 語音擷取需求草稿（降低輸入門檻，H5）
    假設 經紀人傳了一段語音「林先生想找信義區 3房 預算1500到2000萬」
    當 系統經 STT 轉文字並擷取
    那麼 應發出事件 "CustomerRequirementDrafted"
    而且 草稿包含結構化欄位 budget_min=15000000、budget_max=20000000、districts=["信義區"]、room_layout="3房"

  場景: 含 PII 準備建檔時建立 high HITL（Inv-2）
    假設 已有客戶需求草稿且含聯絡方式
    當 系統準備建檔
    那麼 應先建立 risk_level="high" 的 HITL 待核准
    而且 核准前 不應 寫入客戶資料

  場景: HITL 核准後完成建檔
    假設 已有一筆 risk_level="high" 的客戶建檔待核准
    當 經紀人確認
    那麼 應發出事件 "CustomerProfiled"
    而且 需求以結構化形式落地（供配對）

  @gateB
  場景: 隔離未就緒前 mem0 停用（Inv-7 前置，H7）
    假設 Gate B（隔離不變量）尚未驗收通過
    當 系統嘗試呼叫 mem0 寫入客戶記憶
    那麼 呼叫 應 被拒絕（MEM0_ENABLED=false）
    而且 客戶記憶僅使用本地結構化 store

  @gateB
  場景: mem0 寫入帶正確 namespace（Inv-7）
    假設 Gate B 已通過且 MEM0_ENABLED=true
    當 為客戶 "cust-123"（seat-A1, tenantA）寫入軟性記憶
    那麼 mem0 user_id 應 為 "tenantA:seat-A1:cust-123"
    而且 metadata 應 含 tenant_id 與 seat_id
    而且 應發出事件 "CustomerMemoryWritten"

  @gateB
  場景: mem0 不可用時降級不中斷（REL-4）
    假設 Gate B 已通過且 MEM0_ENABLED=true
    當 為客戶 "cust-123" 寫入記憶時 mem0 連線失敗
    那麼 應回傳錯誤碼 "MEM0_UNAVAILABLE"
    而且 應 fallback 至本地結構化 store
    而且 應發出事件 "CustomerMemoryWriteFailed"
    而且 主流程 不應 中斷

  @gateB
  場景: 跨租戶記憶檢索回傳空（Inv-7 二次校驗）
    假設 mem0 中存在屬於 tenantB 的記憶
    當 在 tenantA 的 scope 下檢索
    那麼 ACL 應 過濾掉所有非 tenantA 的記憶
    而且 結果為空並記錄告警

  場景: 建檔後自動排程跟進並主動提醒
    假設 客戶已建檔
    那麼 應發出事件 "FollowUpTaskScheduled"
    當 任務到期
    那麼 Cron 應 主動推播 LINE 提醒
    而且 應發出事件 "FollowUpReminderPushed"

  規則: 冪等推播（Inv-9）

    場景: 相同 idempotency_key 重送被去重
      假設 已有一筆到期跟進任務（idempotency_key=K1）已推播一次
      當 同 K1 的推播第二次被觸發
      那麼 不應 再呼叫 LINE Push API
      而且 "FollowUpReminderPushed" 全程 應 僅發出一次

    場景: 服務重啟後不重發
      假設 推播狀態外移於 Redis，K1 已標記 pushed
      當 服務重啟且 Cron 重掃含 K1 的任務
      那麼 查 Redis 命中 pushed → 應 跳過
      而且 不應 再發出 "FollowUpReminderPushed"
      # action=push_skipped_idempotent
      而且 應發出事件 "AuditTrailRecorded"
