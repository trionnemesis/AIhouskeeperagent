# 領域事件目錄（Domain Events）

> 過去式命名（已發生）。每個事件 payload **必含 envelope**：`tenant_id`, `seat_id`, `occurred_at`, `correlation_id`, `audit_ref`。
> 事件即 Published Language——跨 context 整合一律透過事件，不直接呼叫對方內部。

## Envelope（所有事件共用）

```jsonc
{
  "event": "<EventName>",
  "tenant_id": "string",        // 隔離錨點，NOT NULL
  "seat_id": "string",
  "occurred_at": "ISO-8601",
  "correlation_id": "uuid",     // 串接同一流程
  "causation_id": "uuid|null",  // 觸發本事件的上游事件/命令
  "audit_ref": "AuditTrailId",
  "payload": { /* per-event */ }
}
```

---

## C4 · Content Generation

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `ListingCopyGenerated` | 文案生成完成 | listing_ref, draft_text, model, token_cost | → 進入 HITL 等待核准 |
| `ListingCopyApproved` | 經紀人核准 | copy_id, final_text, edited:bool | → 可用文案清單 read model |
| `ListingCopyRejected` | 經紀人退回 | copy_id, reason | → 重生成或結束 |
| `ViewingBriefingGenerated` | 說帖生成完成 | listing_ref, briefing, **sources[]** | → 附來源標註（Inv-6a） |

> `sources[]` 元素形狀：`{ name: string, url?: string, type: 'metro'|'district'|'school'|'other' }`（對映 `tool-contracts.md` 的 `Source`）。

## C-Listing · Listing Lifecycle

> Matching（Core）的主要觸發源；補上配對 Policy 依賴的上游事件。

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `ListingProfiled` | 物件建檔完成 | listing_id, attributes(district/price/layout/type) | → 觸發配對掃描 |
| `ListingDelisted` | 物件下架 | listing_id, reason | → 從配對候選移除 |

## C5 · Customer & CRM（★Core）

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `CustomerRequirementDrafted` | STT/訊息擷取需求草稿 | draft(budget/district/layout), source:voice\|text | → **強制 HITL**（含 PII） |
| `CustomerProfiled` | 經紀人確認建檔 | customer_id, profile, requirements | → 產生跟進任務 |
| `CustomerMemoryWritten` | 寫入 mem0 | customer_id, **namespace**, mem0_id | ⚠️ 隔離未就緒禁發此事件 |
| `CustomerMemoryWriteFailed` | mem0 不可用 | customer_id, error_code=MEM0_UNAVAILABLE | → fallback 本地 store，主流程不中斷（REL-4） |
| `CustomerRequirementUpdated` | 需求變更 | customer_id, diff | → 觸發配對掃描 |
| `CustomerErasureRequested` | 客戶請求刪除 | customer_id | → HITL(high)（Inv-10） |
| `CustomerErasureApproved` / `CustomerErasureRefused` | HITL 決議 | customer_id, by | → 執行/中止刪除 |
| `CustomerErasureCompleted` | PII 清除 + tombstone + mem0 forget() **完成後**發出的結果事件 | customer_id, tombstoned:true | （forget() 發生於 Approved 與 Completed 之間，見 invariants Inv-10） |

## C6 · Matching（★Core）

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `MatchCandidatesProduced` | 配對掃描完成 | candidates[]（含**命中條件**, 可解釋）, scope | → 通知經紀人（非客戶） |
| `MatchPresented` | 經紀人核准後呈現 | candidate_id, customer_id | （HITL 後） |

## C7 · Interaction & Scheduling

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `FollowUpTaskScheduled` | 建檔/互動後排程 | task_id, due_at, kind, idempotency_key | → 到期觸發推播（C9） |
| `InteractionLogged` | 帶看/斡旋記錄 | customer_id, listing_id, type, note | → 客戶時間軸 |

## C9 · Notification

> 推播事件歸 C9（獨立 Notification BC）；C7 排程、C9 送達，職責分離（對齊 context-map.md）。

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `FollowUpReminderPushed` | Cron 到期推播 | task_id, channel=LINE, **idempotency_key** | → 防重複燒 Push（Inv-9）；冪等命中則記跳過不重發 |

## C8 · Market Intelligence（降級 · 防護）

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `MarketCompProvided` | 通過防護鏈 | comps[], **data_as_of**, confidence, disclaimer, type標註 | （輔助，附延遲聲明） |
| `MarketCompRefused` | 防護攔截 | reason(stale\|garbage\|low_confidence\|addr_mismatch\|source_unavailable) | → 寧可不答（source_unavailable=REL-4 降級） |
| `GarbageDataFiltered` | TimestampGuard 命中 | filtered_count, samples(2101/2033…) | → 稽核 + 監控 |

## C2 · Governance（Cross-cutting）

| Event | 觸發 | payload 重點 | 後續 Policy |
|---|---|---|---|
| `HITLApproved` | 人工放行 | subject_ref, by, at | → 執行原動作 |
| `HITLRejected` | 人工駁回 | subject_ref, by, reason | → 中止動作 |
| `AuditTrailRecorded` | 任何 command/event | actor, action, scope, payload_hash | append-only |
| `MispricingReported` | 房仲回報錯價 | source_ref, description | → **北極星反指標 +1 + 停損檢討** |
| `UnauthorizedAccessBlocked` | 無法解析 scope / 未 allowlist | line_user_id(脫敏), reason | → 前置拒絕，不進對話 + 稽核 |
| `TenantScopeViolationDetected` | 偵測越界存取（scope 已解析但跨租戶） | attempted_scope, blocked:true | → 阻擋 + 告警（不應發生） |
| `PiiAccessLogged` | 存取 PII 欄位 | field, purpose, by | → 稽核 |

---

## 事件因果鏈範例（客戶記憶流程）

```
CustomerRequirementDrafted
  → (HITL) HITLApproved
    → CustomerProfiled
      → CustomerMemoryWritten          (causation = CustomerProfiled)
      → FollowUpTaskScheduled          (causation = CustomerProfiled)
        → (due) FollowUpReminderPushed (causation = FollowUpTaskScheduled)
      → MatchCandidatesProduced        (causation = CustomerProfiled, 若有新需求)
（全程旁路）→ AuditTrailRecorded × N
```
