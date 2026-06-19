# language: zh-TW
@p0 @governance
功能: per-tenant 並發限流（Concurrency Gate, REL-2）
  作為 平台
  我要 限制每租戶同時執行的 agent run 數
  以便 突發訊息不耗盡 token/Push 預算（H6：原無 Semaphore）

  背景:
    假設 per-tenant 並發上限為 3（PER_TENANT_MAX_CONCURRENT_RUN）
    而且 並發狀態外移於 Redis

  規則: 同一租戶並發 agent run 不超過上限

    場景: 同時 N+1 筆只執行 N 筆，其餘排隊
      假設 租戶 "信義加盟A店" 已有 3 筆 agent run 進行中
      當 第 4 筆訊息進入
      那麼 第 4 筆 應 被排隊等待
      而且 應回傳錯誤碼 "CONCURRENCY_LIMITED"
      當 任一進行中的 run 完成
      那麼 排隊的第 4 筆 應 被釋放執行

    場景: 不同租戶並發互不影響
      假設 租戶 "信義加盟A店" 已達 3 筆並發上限
      當 租戶 "永慶直營B店" 進來 1 筆訊息
      那麼 該訊息 應 立即執行
      而且 不應 受 A 店並發狀態影響

  規則: 並發狀態外移，重啟不卡死

    場景: 服務重啟後並發計數可恢復
      假設 Redis 記錄租戶 "信義加盟A店" 有 2 筆進行中
      當 服務重啟
      那麼 並發計數 應 由 Redis 恢復
      而且 不應 因 in-memory 遺失而永久占用名額
