# 統一錯誤模型（Error Model）

> 補 [`tool-contracts.md`](tool-contracts.md) L「錯誤以結構化 error（非拋字串）」之缺口。所有 MCP server / Gateway / ACL 共用同一 `DomainError` 形狀與錯誤碼目錄，BDD step 一律斷言 `code`（非字串字面值）。

## DomainError envelope

```ts
interface DomainError {
  code: ErrorCode;          // 見下方目錄
  category: 'SCOPE' | 'SYSTEM' | 'DOMAIN' | 'HITL' | 'EXTERNAL';
  retryable: boolean;       // 呼叫端可否重試
  userMessage: string;      // 對經紀人顯示的安全訊息（不含 PII/堆疊）
  auditRef: string;         // 對應 audit_logs（Inv-3）
  sourceRef?: string;       // 出錯來源（comp/copy/msg id），供 error_reports
  detail?: Record<string, unknown>; // 內部診斷，預設不外送
}
```

> **語意拒絕 vs 錯誤**：行情「拒答」（`MarketCompRefused`）是**正常領域結果**（Inv-5），用 `outcome:'refused'` 表達，**不是** `DomainError`。`DomainError` 僅用於「無法完成」的失敗。

## 錯誤碼目錄

| code | category | retryable | 觸發 | 對應 |
|---|---|---|---|---|
| `SCOPE_UNRESOLVED` | SCOPE | false | LINE userId 無法解析 (tenant,seat) | Inv-1, UnauthorizedAccessBlocked |
| `SCOPE_NOT_ALLOWLISTED` | SCOPE | false | 已綁定但未授權 | Inv-1 |
| `SCOPE_VIOLATION` | SCOPE | false | 跨租戶存取企圖 | Inv-1, TenantScopeViolationDetected |
| `HITL_PENDING` | HITL | true（核准後） | 動作待人工核准 | Inv-2 |
| `HITL_REJECTED` | HITL | false | 人工駁回 | Inv-2 |
| `HITL_TIMEOUT` | HITL | false | HITL Pending 逾時自動駁回 | Inv-2, 見 state-machines |
| `MEM0_DISABLED` | DOMAIN | false | Gate B 未過，`MEM0_ENABLED=false` | Inv-7 |
| `MEM0_UNAVAILABLE` | EXTERNAL | true | mem0 連線失敗 → fallback 本地 | REL-4 |
| `MARKET_SOURCE_UNAVAILABLE` | EXTERNAL | true | lvr 連線超時/5xx | REL-4 |
| `SOURCE_QUOTA_EXCEEDED` | EXTERNAL | true | 外部源每日次數/連線上限耗盡（GCIS/TDX） | DI-8 |
| `BUDGET_EXCEEDED` | DOMAIN | false | session token/iteration 上限**且無可回傳草稿**時 | COST-1 |
| `CONCURRENCY_LIMITED` | SYSTEM | true | per-tenant Semaphore 滿 | REL-2 |
| `PII_WRITE_BLOCKED` | DOMAIN | false | 未過治理最小集時寫真 PII | Inv-8 |
| `VALIDATION_FAILED` | DOMAIN | false | 輸入不合規 | — |
| `SYSTEM_INTERNAL` | SYSTEM | false | 未預期錯誤 | — |

## 可重試矩陣

| 情境 | retryable | 呼叫端行為 |
|---|---|---|
| `HITL_PENDING` | true | 等核准事件，不重打工具 |
| `MEM0_UNAVAILABLE` / `MARKET_SOURCE_UNAVAILABLE` / `SOURCE_QUOTA_EXCEEDED` | true | 指數退避；超過上限 → 降級（拒答/暫停記憶，REL-4），不崩 |
| `CONCURRENCY_LIMITED` | true | 排隊重試 |
| `SCOPE_*` / `*_REJECTED` / `BUDGET_EXCEEDED` | false | 終止並回報 |

## MCP / HTTP 對映

- MCP 工具：失敗回傳 `{ error: DomainError }`；領域「拒答」回傳正常結果含 `outcome:'refused', reason:<ErrorCode 子集>`。
- HTTP（Gateway）：`category` → status（SCOPE→403、HITL_PENDING→202、EXTERNAL→503、VALIDATION→400、SYSTEM→500）。
- `category ≥ DOMAIN` 且涉客戶可見後果 → 寫 `error_reports`（北極星）+ `AuditTrailRecorded`。

## 與 market-comp reason 對齊

`MarketCompRefused.reason`（主 spec C8 market-comp-mcp）五值 = `stale` | `garbage` | `low_confidence` | `addr_mismatch` | `source_unavailable`。其中**僅 `source_unavailable` 對映 ErrorCode** `MARKET_SOURCE_UNAVAILABLE`（外部源失效→降級拒答，REL-4）；其餘 4 個是**純領域 refused reason**（正常結果語意，非 `DomainError`）。

資料層 `lvr-mcp.query_market`（見 [`../05-data-mcp/lvr-mcp.md`](../05-data-mcp/lvr-mcp.md)）沿用上述五值，並**新增純領域 reason `insufficient_comps`**（可比交易筆數不足）；`insufficient_comps` 同為純領域 refused，**不**對映 ErrorCode。

## COST-1 / iteration budget 行為

達 `ITERATION_BUDGET` 上限時：**有草稿 → 回傳目前最佳草稿（成功結果，非錯誤）**並記 `token_cost`；**無任何草稿可回 → `BUDGET_EXCEEDED`（DomainError）**。`configuration.md` 與 `phase1-listing-copywriting.feature` 以「回最佳草稿」描述前者，與此一致。
