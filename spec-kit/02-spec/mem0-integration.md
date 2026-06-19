# mem0 MCP 整合規格

> mem0 作為**結構化客戶記憶**的長期記憶層（C5 Core Domain）。透過 **ACL** 接入，**強制 tenant-scoped**。

## 硬前提（不可協商）

> ⛔ **隔離不變量（Inv-1）未驗收前，mem0 全面停用。**（審查硬條件，Hotspot H7）
> 在 Gate B 通過前，C5 以本地結構化 store（`customers` / `customer_requirements`）運作，**不接 mem0**。

## 為什麼 mem0 需要 ACL

mem0 是不受控的外部記憶服務。若直接讓 Hermes memory_provider 裸接，prompt injection 或檢索越界即跨租戶 PII 外洩。ACL 的職責：

1. **命名空間強制（Inv-7）**：所有寫入/檢索的 `user_id` = `${tenant_id}:${seat_id}:${customer_id}`。
2. **scope 二次校驗**：檢索回來的每筆 memory，於應用層再驗 `metadata.tenant_id === ctx.tenant_id`，不符即丟棄並告警 `TenantScopeViolationDetected`。
3. **PII 脫敏（Inv-8）**：寫入 mem0 的內容預設脫敏（電話/身分證→代號），原值留本地 tenant scope。
4. **可關閉開關**：feature flag `MEM0_ENABLED`，預設 `false`，Gate B 綠燈才開。

## 命名空間規範（Inv-7）

```
user_id   = `${tenant_id}:${seat_id}:${customer_id}`   // 主隔離鍵
metadata  = { tenant_id, seat_id, customer_id, source: "voice|text" }
filters（檢索）= { AND: [ {tenant_id}, {seat_id} ] }     // 雙重保險
```

> 採 `user_id` 複合鍵 + `metadata.tenant_id` filter **雙層**：即使 mem0 端 filter 失效，複合 user_id 仍隔離；檢索後應用層再校驗第三層。

## ACL 介面（TypeScript 契約）

```ts
interface Mem0Acl {
  // 寫入：ctx 提供 scope，內容先脫敏
  write(ctx: TenantScope, customerId: string, memory: RedactedMemory): Promise<MemoryRef>;
  // 檢索：強制 scope filter + 回傳後二次校驗
  search(ctx: TenantScope, customerId: string, query: string): Promise<ScopedMemory[]>;
  // 刪除（客戶封存/被遺忘權）
  forget(ctx: TenantScope, customerId: string): Promise<void>;
}

interface TenantScope { tenantId: string; seatId: string; }
```

- 任何呼叫缺 `ctx.tenantId` → 直接拋錯（不送 mem0）。
- `search` 回傳前過濾 `m.metadata.tenant_id === ctx.tenantId && m.metadata.seat_id === ctx.seatId`。
- 全部呼叫產生 `AuditTrailRecorded`；命中 PII 產 `PiiAccessLogged`。
- `forget()` 由 **Inv-10 被遺忘權流程**驅動：`CustomerErasureApproved`（HITL 核准）後呼叫，清整個 customer namespace；屬資料保留政策的一部分（見 [`../01-domain/invariants.md`](../01-domain/invariants.md) Inv-10）。
- mem0 不可用時：寫入降級為 fallback 本地結構化 store，發 `CustomerMemoryWriteFailed`，主流程不中斷（REL-4，錯誤碼 `MEM0_UNAVAILABLE`）。

## 與 Hermes memory_provider 的關係

- Hermes `agent/memory_provider.py` 是抽象框架（🟡）。
- 不直接把 mem0 掛成 Hermes provider；改由 **C5 customer-crm-mcp（Node.js）** 經 Mem0Acl 操作，再以 MCP 工具結果回饋對話。
- 理由：把 scope 強制與校驗留在我們能控制的 Node.js ACL，而非 Hermes 內部。

## 結構化 store vs mem0 分工

| 資料 | 存放 | 理由 |
|---|---|---|
| 預算/區域/房型（配對用） | **本地 `customer_requirements`（結構化）** | 精準 SQL WHERE 配對，可解釋 |
| 對話脈絡/偏好/軟性記憶 | **mem0**（語意檢索） | 自然語言回憶 |
| PII 原值 | **本地（脫敏外送）** | Inv-8 |

> 配對（C6）**只**用本地結構化資料，不依賴 mem0 語意檢索（可解釋 + 無外送）。

## 驗收

- [`../03-features/phase2-customer-memory.feature`](../03-features/phase2-customer-memory.feature)：含「mem0 寫入帶正確 namespace」「跨租戶檢索回傳空」「Gate B 未過時 mem0 停用」場景。
