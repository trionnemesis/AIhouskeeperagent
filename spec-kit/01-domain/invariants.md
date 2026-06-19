# 治理不變量（Governance Invariants）

> **這是 P0 上線 blocker，不是後補功能。** 每條不變量都是**永遠為真**的硬約束，違反即視為缺陷（不是「待辦」）。
> 對應 BDD 驗收見 [`../03-features/`](../03-features/)；資料層落地見 [`../02-spec/erm.dbml`](../02-spec/erm.dbml)。

## 不變量總表

| ID | 名稱 | 一句話 | 違反後果 | Gate |
|---|---|---|---|---|
| **Inv-1** | 租戶隔離 | 所有業務資料讀寫硬約束 `WHERE tenant_id=?` | 跨客戶 PII 外洩 | B |
| **Inv-2** | HITL 放行 | 對外訊息 / 寫入動作必經人工核准 | 誤發 / 誤寫，法律責任 | B |
| **Inv-3** | 稽核不可變 | 每個 command/decision 產 append-only 軌跡 | 無免責證據鏈 | B |
| **Inv-4** | 時間戳防呆 | 拒絕 `trade_date <2010` 或 `>今日+90天` 的列 | 餵出 2101 垃圾值→錯價 | B（行情前置） |
| **Inv-5** | 拒答優於猜測 | 地址比對失敗 / 信心 < 閾值 → 拒答 | 錯價→永久棄用 | （Phase3 前置） |
| **Inv-6** | 行情標註義務 | 行情輸出必附 `data_as_of` + 物件類型標註 | 房仲誤用過時資料 | （Phase3 前置） |
| **Inv-7** | 記憶命名空間 | mem0 namespace 必為 `tenant:seat:customer` | 跨租戶記憶越界 | B（mem0 前置） |
| **Inv-8** | PII 最小揭露 | 日誌 / 外送預設脫敏，原值僅 tenant scope 內 | 個資外洩 | B |
| **Inv-9** | 冪等推播 | 推播帶 idempotency_key，重啟不重發 | 重複燒 LINE Push 計費 | （Phase2 前置） |
| **Inv-10** | 資料保留 / 被遺忘權 | 各表有保留期；客戶可請求刪除，刪除與 append-only audit 並存 | 個資法合規缺口 | B |
| **Inv-6a** | 外部資料溯源 | 非行情的外部資料（捷運/學區等）輸出須附來源 | 杜撰/不可追溯 | （Phase1 前置） |

---

## Inv-1 · 租戶隔離（Tenant Isolation）

**規範**：每張承載業務/客戶資料的表都有 `tenant_id NOT NULL`；所有 query、所有 RAG 檢索、所有配對，在資料存取層**強制注入** `WHERE tenant_id = :ctx.tenant_id`，無 `tenant_id` 的 query 一律拒絕執行。

**為什麼**：`session_key` 是會話路由 key，**不是**租戶資料邊界（報告 2.4）。prompt injection 或 RAG 越界即跨客戶 PII 外洩（H1）。

**落地手段**：
- 資料存取層統一經 `TenantScopeResolver` 注入 scope（不允許裸 SQL 繞過）。
- MVP 採**部署隔離**（一店一 Hermes home + 一組 Node.js 服務綁單一 tenant_id）作為過渡，仍在資料層保留 `tenant_id` 欄位與約束，規模化再升級為應用層多租戶。
- 測試：跨租戶查詢必須回傳空集合且記錄 `TenantScopeViolationDetected`。

**測試策略（部署隔離下仍須驗）**：MVP 部署隔離單租戶 DB 沒有第二租戶可測「跨租戶回空」，故：
1. CI 以 **seeded dual-tenant fixture** 跑 [`phase0-tenant-isolation.feature`](../03-features/phase0-tenant-isolation.feature)（即使 prod 為單租戶）。
2. `TenantScopeResolver` / scope-helper 單元測試含 multi-tenant matrix（跨租戶讀寫→回空 + 告警）。
3. 資料存取層（Drizzle/Kysely typed query builder）**compile-time 強制注入 scope，禁裸 SQL 繞過**。

## Inv-2 · HITL 放行（Human-in-the-loop Gate）

**規範**：以下動作在 `HITLApproved` 前**不得執行**：
- 任何**對外**訊息（發給客戶 / 第三方）。
- 任何**寫入**客戶業務系統（建檔、改價、發佈、寄送）。
- 任何 `risk_level = High` 的動作（含 PII 建檔、行情對外引用）。

**為什麼**：Agent 誤發訊息給錯客戶 / 基於垃圾值給錯建議 = 直接商業損害 + 法律責任。HITL 軌跡同時是**法律免責證據鏈**。

**例外**：純讀取、產生「僅給經紀人本人看的草稿」不需 HITL（但草稿不得外流）。

**逾時**：HITL `Pending` 超過 `HITL_PENDING_TIMEOUT_HOURS`（暫定 72h）自動轉 `Rejected`（reason=`approval_timeout`，錯誤碼 `HITL_TIMEOUT`），避免動作懸置。狀態機見 [`../02-spec/governance-state-machines.md`](../02-spec/governance-state-machines.md)。

## Inv-3 · 稽核不可變（Append-only Audit）

**規範**：`audit_logs` 為 append-only（無 UPDATE/DELETE 權限）；記錄 actor、action、scope、payload 雜湊、時間。codebase 原無 audit_log table（報告 §8 已複核），需新增。

## Inv-4 · 時間戳防呆（TimestampGuard）

**規範**：任何來自 lvr-trades 的列，`trade_date < 2010-01-01` 或 `> 今日 + 90 天` **一律剔除**，並記 `GarbageDataFiltered`。

**為什麼**：實測 `MAX(iso_trade_date)=2101-10-17`、`MIN=1921-01-28`；naive 查詢會餵出未來日期（H3）。**任何未加上界防呆的「最新行情」查詢都會回傳 2101 垃圾值**。

```js
// 參考實作（Node.js, C8 ACL 內）
const LOWER = Date.parse('2010-01-01');
const upper = Date.now() + 90 * 864e5;
const guarded = rows.filter(r => {
  const t = Date.parse(r.iso_trade_date);
  return Number.isFinite(t) && t >= LOWER && t <= upper;
});
```

## Inv-5 · 拒答優於猜測（Refuse over Guess）

**規範**：地址比對失敗、可比交易筆數不足、或 `ConfidenceScore < 閾值` → 輸出 `MarketCompRefused`，**不得**輸出推測價。

**為什麼**：房仲對錯價零容忍，錯一次永久棄用（牆 1）。

## Inv-6 · 行情標註義務（Disclosure）

**規範**：`MarketCompProvided` 必附：`data_as_of`（資料更新至 YYYY-MM）、預售/成屋/車位/有無管理費標註、信心分數、來源。話術為「近 N 季官方彙整 + 趨勢」，**禁稱「即時」**。報告實測定錨：最新交易季 = **115S1（2026 Q1）**、最新有效交易日 **2026-03-05**（今日 2026-06，延遲約 3 個月）。

## Inv-6a · 外部資料溯源（External Data Provenance）

**規範**：非行情的外部資料輸出（帶看說帖的捷運/行政區/學區等）必附**來源標註**；無法確認者標「請以官方公告為準」，不杜撰。與 Inv-6（專指行情 `data_as_of`）區分，避免以「精神」鬆散借用 Inv-6。

## Inv-7 · 記憶命名空間（mem0 Namespace）

**規範**：所有 mem0 寫入/檢索的 namespace（user_id/metadata filter）**必為** `${tenant_id}:${seat_id}:${customer_id}`；檢索結果再於應用層二次校驗 scope。隔離不變量（Inv-1）未驗收前，**mem0 全面停用**（審查硬條件，H7）。詳見 [`../02-spec/mem0-integration.md`](../02-spec/mem0-integration.md)。

## Inv-8 · PII 最小揭露（PII Minimal Disclosure）

**規範**：PII 欄位（身分證/財務/電話/地址）序列化到日誌、LLM prompt、外部服務時**預設脫敏**；原值僅在 tenant scope 內、且經 `PiiAccessLogged` 後存取。MVP 治理最小集可採「**不寫真 PII，用代號/脫敏**」（報告 §3.3）。

## Inv-9 · 冪等推播（Idempotent Push）

**規範**：每則 LINE Push 帶 `idempotency_key`（= `correlation_id + kind + due_at`，皆建檔前已決定，避免以 task_id 自我參照）；唯一性以 `(tenant_id, idempotency_key)` 範圍化（非全表 unique）；dedup 與 reply token 狀態**外移**（Redis/SQLite），重啟不重發。

**為什麼**：in-memory dict 重啟即遺失 → LINE 重送造成重複回覆 + 重複燒 Push 計費（H2）。

## Inv-10 · 資料保留與被遺忘權（Retention & Right to Erasure）

**規範**：
1. **保留期**：各表設保留期（`DATA_RETENTION_DAYS`，待法務定）；逾期 PII 欄位匿名化。
2. **刪除流程**：`CustomerErasureRequested` → HITL(high) → `CustomerErasureApproved`（或 `CustomerErasureRefused`）→ 刪 PII 欄位 + 業務記錄 tombstone（`status=erased`, `deleted_at`）+ `Mem0Acl.forget()`（清 mem0 namespace）→ `CustomerErasureCompleted`。
3. **與 Inv-3 並存**：`audit_logs` 為 append-only 不刪，但**脫去關聯 PII**（僅留 `payload_hash` 與匿名化 scope），兼顧「被遺忘」與「稽核留存」。

**為什麼**：個資法強制；PII「進得來」必須有「出得去」的政策，否則與 Phase 0 PII 治理定位矛盾。落地：`customers.deleted_at`（見 [`../02-spec/erm.dbml`](../02-spec/erm.dbml)）、`forget()`（見 [`../02-spec/mem0-integration.md`](../02-spec/mem0-integration.md)）、`archive_customer` 工具（見 [`../02-spec/tool-contracts.md`](../02-spec/tool-contracts.md)）。

---

## 治理閘執行順序（GovernanceGate pseudo-flow）

```
inbound command
  1. TenantScopeResolver → 解析 (tenant_id, seat_id)；無 scope → 拒絕 (Inv-1)
  2. 風險判定 → Low / High（含 PII？對外？寫入？）
  3. 資料存取一律注入 WHERE tenant_id=? (Inv-1)；PII 脫敏 (Inv-8)
  4. 若 High 或 對外/寫入 → 建立 HITLApproval (Inv-2)，暫停
  5. 旁路：AuditTrailRecorded (Inv-3)
  6. （行情類）MispricingGuard：Inv-4/5/6
outbound effect 僅在 HITLApproved 後發生
```

> 設計刻意讓「技術治理」= 「法律免責證據鏈」同構：HITL / 來源提示 / 信心分數 / 異常過濾 / 稽核軌跡，既是品質賣點，也是責任邊界證據。
