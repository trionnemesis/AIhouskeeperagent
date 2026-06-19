# Domain Tool / MCP 契約

> 領域能力以 **MCP servers（Node.js/TypeScript）** 接給 Hermes 工具系統。所有工具**第一參數為 `ctx`（TenantScope）**，由 GovernanceGate 注入；工具內部一律經 scope 化的資料存取層（Inv-1）。

## 共通約定

- 所有工具呼叫前置：`GovernanceGate` 已注入 `ctx = { tenantId, seatId }`；缺 scope 直接拒絕。
- 所有「寫入 / 對外」工具回傳 **draft + 待 HITL** 狀態，不直接生效（Inv-2）。
- 所有工具產生 `AuditTrailRecorded`（Inv-3）。
- 回傳型別標註明確；錯誤以結構化 `DomainError`（非拋字串），錯誤碼與形狀見 [`error-model.md`](error-model.md)。領域「拒答」（如行情）是正常結果 `outcome:'refused'`，非 `DomainError`。

---

## content-gen-mcp（C4）

```ts
// 生成物件文案草稿（不外流，待 HITL）
generate_listing_copy(ctx, {
  listingId: string, kind: 'title'|'description', tone?: string, photos?: ImageRef[]
}): { copyId: string, draftText: string, hitlId: string }   // status=draft

// 生成帶看說帖（唯讀，附來源）
generate_viewing_briefing(ctx, {
  listingId?: string, address?: string, district: string
}): { briefing: string, sources: Source[] }   // 含捷運/學區來源 (Inv-6a 外部資料溯源)

// Source: 外部地理資料來源標註（Inv-6a）
interface Source { name: string; url?: string; type: 'metro'|'district'|'school'|'other' }
```

## customer-crm-mcp（C5 · ★Core）

```ts
// 從語音/訊息擷取需求草稿（不建檔，待 HITL）
draft_customer_requirement(ctx, {
  rawText: string, source: 'voice'|'text'
}): { draft: RequirementDraft, hitlId: string, piiDetected: boolean }

// HITL 核准後建檔（結構化）
profile_customer(ctx, {
  hitlId: string, profile: CustomerProfile, requirement: Requirement
}): { customerId: string }   // 觸發 CustomerProfiled

// 寫入軟性記憶（mem0 ACL，Gate B 後才可用）
remember_customer(ctx, {
  customerId: string, memory: string
}): { memoryRef: string }    // namespace 強制 (Inv-7)；MEM0_ENABLED=false 時拒絕

// 檢索客戶脈絡（scope 強制 + 二次校驗）
recall_customer(ctx, { customerId: string, query: string }): ScopedMemory[]

// 客戶封存 / 被遺忘權（Inv-10）：提案待 HITL，核准後才執行
archive_customer(ctx, {
  customerId: string, reason?: string
}): { hitlId: string }   // 觸發 CustomerErasureRequested；核准後 status→erased + mem0.forget() + tombstone；LLM 可見但不可逕自生效 (Inv-2)
```

## matching-mcp（C6 · ★Core）

```ts
// 結構化配對：SQL WHERE（可解釋、無外送）
match_listings(ctx, {
  customerId: string
}): { candidates: { listingId: string, matchedOn: string[], score: number }[] }
// 硬約束 WHERE tenant_id=?（Inv-1）；matchedOn 標明命中條件（可解釋）

match_customers(ctx, { listingId: string }): { candidates: {...}[] }
```

## market-comp-mcp（C8 · ACL · 重防護）

```ts
// 行情查詢（降級為輔助；經完整防護鏈）
query_market_comp(ctx, {
  address?: string, district: string, buildingType: string
}):
  | { outcome: 'provided', comps: Comp[], dataAsOf: string,
      confidence: number, disclaimer: string }   // Inv-6 標註
  | { outcome: 'refused', reason: 'stale'|'garbage'|'low_confidence'|'addr_mismatch'|'source_unavailable' }
// 內部強制：TimestampGuard(Inv-4) → 單價檢核 → 信心評分(Inv-5)
```

## notify-mcp（C9）

```ts
// 排程跟進任務（冪等）
schedule_follow_up(ctx, {
  customerId?: string, kind: string, dueAt: string
}): { taskId: string, idempotencyKey: string }   // Inv-9
```

## governance（C2 · 由 Gate 內部使用，非 LLM 直呼）

```ts
resolve_scope(lineUserId: string): TenantScope | null          // Inv-1
open_hitl(ctx, subject): { hitlId: string }                    // Inv-2
record_audit(ctx, action, payloadHash, piiAccessed): void      // Inv-3
report_error(ctx, { category, sourceRef, description }): void  // 北極星反指標
```

---

## 工具暴露原則

- LLM **可見**：content-gen、customer-crm（draft/recall）、matching、market-comp、notify。
- LLM **不可見**（僅 Gate/系統呼叫）：governance.resolve_scope / open_hitl / record_audit。
- 高風險工具（profile_customer、query_market_comp、對外送）一律走 HITL，LLM 只能「提案」不能「生效」。
