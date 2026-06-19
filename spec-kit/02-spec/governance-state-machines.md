# 狀態機與端到端序列圖

> 補各 `status` 列舉缺乏轉移圖、逾時行為與跨 context 序列的缺口。Mermaid 可直接渲染。

## HITLApproval 狀態機（Inv-2）

```mermaid
stateDiagram-v2
  [*] --> Pending: open_hitl (risk=high 或 對外/寫入)
  Pending --> Approved: 經紀人核准/編輯
  Pending --> Rejected: 經紀人駁回
  Pending --> TimedOut: 逾 HITL_PENDING_TIMEOUT_HOURS(72h)
  TimedOut --> Rejected: 自動轉駁回 (reason=approval_timeout, HITL_TIMEOUT)
  Approved --> [*]: 原動作執行
  Rejected --> [*]: 原動作中止
```

- **終態**：`Approved`、`Rejected`（含 timeout 轉入）。
- **逾時**：Pending 超過 72h 自動 `TimedOut→Rejected`，避免動作懸置；發 `HITLRejected(reason=approval_timeout)`。
- 與 reply token（50s TTL）關係：HITL 屬**非同步**流程，不受 50s reply token 限制；逾 45s 走慢回應 Template Buttons（REL-3），HITL 卡本身用 push 發送。

## MarketCompQuery 狀態機（Inv-4/5/6）

```mermaid
stateDiagram-v2
  [*] --> Pending: query_market_comp
  Pending --> Guarding: 取得 raw_rows
  Guarding --> Refused: TimestampGuard 後無有效列 / addr_mismatch / confidence<閾值 / source_unavailable
  Guarding --> Provided: 通過防護 + 足夠可比交易
  Provided --> [*]: 附 data_as_of + 信心 + 類型標註
  Refused --> [*]: 寧可不答 (reason)
```

- **終態**：`Provided`、`Refused`（皆唯讀結果，非錯誤）。

## FollowUpTask 狀態機（Inv-9）

```mermaid
stateDiagram-v2
  [*] --> Pending: schedule_follow_up
  Pending --> Pushed: 到期 + 冪等檢查未命中 → Cron 推播
  Pending --> Pushed: 到期 + 冪等命中 → 跳過實際 Push（仍記跳過）
  Pending --> Canceled: 客戶封存/任務取消
  Pushed --> Done: 經紀人標記完成
  Done --> [*]
  Canceled --> [*]
```

## Listing 狀態機（見 [`../01-domain/domain-events.md`](../01-domain/domain-events.md) Listing Lifecycle）

```mermaid
stateDiagram-v2
  [*] --> Open: ListingProfiled
  Open --> Reserved: 斡旋中
  Open --> Closed: 成交
  Open --> Delisted: ListingDelisted(reason)
  Reserved --> Open: 斡旋破局
  Reserved --> Closed: 成交
  Closed --> [*]
  Delisted --> [*]
```

## 端到端序列：LINE 訊息 → HITL → 對外（Inv-1/2/3）

```mermaid
sequenceDiagram
  participant U as 客戶/經紀人(LINE)
  participant GW as Node Gateway
  participant R as TenantScopeResolver
  participant G as GovernanceGate
  participant H as Hermes Runtime
  participant M as Domain MCP
  participant A as AuditTrail
  U->>GW: webhook(訊息) [HMAC 驗章 @ Gateway]
  GW->>R: resolve(line_user_id)
  R-->>GW: (tenant,seat) | SCOPE_UNRESOLVED→拒絕+audit
  GW->>G: inbound command + ctx
  G->>A: AuditTrailRecorded(inbound)
  G->>H: 轉對話 (注入 scope)
  H->>M: tool call (ctx)
  M-->>H: draft（對外/寫入→需 HITL）
  H->>G: 提案 outbound/write
  G->>U: HITL Flex 卡(push) [Pending]
  U->>GW: 點選 核准/駁回
  GW->>G: HITL decision
  G->>A: HITLApproved/Rejected + AuditTrailRecorded
  alt Approved
    G->>U: 送出對外訊息 / 執行寫入（記 outbound_messages）
  else Rejected/TimedOut
    G-->>H: 中止
  end
```

> 逾時點標註：reply token 50s（同步回覆窗）、HITL Pending 72h（非同步核准窗）。
