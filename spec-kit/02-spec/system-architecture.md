# 系統架構規格

> 底座 **Hermes-Agent**（Python runtime, pinned）+ **Node.js** 領域/治理/整合層 + **mem0 MCP**（記憶）+ **LINE**（觸點）。

## 設計取捨：Hermes 是 Python，新 code 寫在 Node.js

Hermes-Agent 是 Python codebase（`run_agent.py` 5,115 行、`conversation_loop.py`、`hermes_state.py`）。使用者要求 **Node.js 寫程式**。兩者如此協調：

- **Hermes（Python，pinned，零核心改動複用）**：承載對話迴圈、LINE adapter、STT、prompt builder、Cron、工具派發。作為 **Agent Runtime / Host**。
- **Node.js（所有新領域邏輯）**：domain 能力以 **MCP servers** 形式接給 Hermes 工具系統；治理 middleware + 多租戶 LINE 邊界 + 領域資料庫由 Node.js 擁有。

> Hermes「零核心改動可擴充」指的是**加工具**的擴充性。多租戶/計費歸戶若走應用層會需動核心——故 MVP 走**部署隔離**規避（見下）。

---

## C4 容器圖（MVP · 部署隔離模式）

```
                          🩷 LINE Platform
                                │ webhook (HMAC-SHA256)
                                ▼
        ┌───────────────────────────────────────────────┐
        │  Node.js: Tenant Edge Gateway                  │  ← 新增 🔴
        │  · 多租戶路由 (userId→tenant,seat)             │
        │  · 簽章驗證 / dedup (Redis, 冪等 Inv-9)        │
        │  · GovernanceGate (scope注入/風險/HITL/audit)  │
        └───────────────────────────────────────────────┘
                                │ (per-tenant) OpenAI-compatible / internal API
                                ▼
        ┌───────────────────────────────────────────────┐
        │  Hermes Agent Runtime  (Python, pinned) 🟢     │
        │  · conversation_loop (ReAct)                   │
        │  · prompt_builder / context_compressor         │
        │  · STT / Cron scheduler / Tool dispatch        │
        │  · LINE adapter: reply/push 出口；webhook 入口停用│
        └───────────────────────────────────────────────┘
            │ MCP / tool call  (Hermes 不直連 mem0)
            ▼
  ┌────────────────────────────────────┐
  │ Node.js Domain MCP Servers  🔴 新增  │
  │  · content-gen-mcp  (C4)            │
  │  · customer-crm-mcp (C5) ─ACL─▶ 🩷 mem0 MCP  (namespace 強制 tenant:seat:customer, Inv-7)
  │  · matching-mcp     (C6)            │
  │  · notify-mcp       (C9)            │
  │  · market-comp-mcp  (C8) ─ACL─▶ 🩷 lvr-trades MCP (TimestampGuard Inv-4)
  └────────────────────────────────────┘
            │ 擁有
            ▼
  ┌───────────────────────────┐
  │ Domain DB (Postgres/SQLite)│  tenant_id 欄位 + 約束 (Inv-1)
  │  + audit_logs (append-only)│  (Inv-3)
  └───────────────────────────┘
```

> **記憶資料流（修正 H7 越界風險）**：Hermes `memory_provider` **不接 mem0**；記憶一律經 **C5 customer-crm-mcp 的 Mem0Acl** 操作，強制 `tenant:seat:customer` namespace 與 scope 二次校驗（Inv-7/Inv-1）。Hermes 對話迴圈透過 `recall_customer` MCP 工具取回已 scope 化的記憶結果，而非直接讀 mem0。詳見 [`mem0-integration.md`](mem0-integration.md)。

### 部署隔離（MVP）vs 應用層多租戶（Scale）

| | MVP：部署隔離 | Scale：應用層多租戶 |
|---|---|---|
| 單位 | 一店/一租戶 = 一組 Hermes home + Node.js 服務（綁單一 tenant_id） | 共用實例，`tenant_id` 欄位區隔 |
| 隔離強度 | 進程/檔案系統級（最強） | 應用層約束（Inv-1） |
| 動核心？ | 否（規避報告警示） | 是（計費歸戶/分庫） |
| 何時 | Phase 0–2 | 拒單排隊 + 複用率驗證後 |

> 兩模式**都**在資料層保留 `tenant_id` 與 Inv-1 約束，確保升級平滑。

---

## 技術選型（Node.js 層）

| 關注點 | 選型 | 理由 |
|---|---|---|
| 語言/型別 | **TypeScript（strict）** | 公開介面強型別（個人偏好：strict type hints） |
| MCP SDK | `@modelcontextprotocol/sdk` | domain 能力以 MCP 接 Hermes |
| Runtime | Node.js LTS | |
| Web/Gateway | Fastify | 輕量、schema 驗證內建 |
| DB | Postgres（prod）/ SQLite（dev） | 結構化配對需 SQL；與 Hermes SQLite 風格一致 |
| ORM/Query | Drizzle / Kysely（型別安全 + 強制 scope helper） | 在資料存取層統一注入 `WHERE tenant_id` |
| 狀態外移 | Redis | dedup / reply token / 冪等（Inv-9, H2） |
| 記憶 | mem0（透過 MCP / SDK，ACL 包裝） | 報告指定；tenant-scoped |
| STT | 複用 Hermes（Groq whisper-large-v3-turbo） | 🟢 現成 |
| 模型路由 | 複用 Hermes provider（分層：Flash 查詢/文案、Claude 議價/說帖、本機 Qwen PII） | token budget 守毛利 |
| DI | 建構式注入（DI > 直接實例化） | 個人偏好 |
| 測試 | Vitest（unit）+ Cucumber.js（BDD `.feature`）| BDD 場景可執行 |

---

## 依賴方向（Dependency Rule）

```
LINE Edge Gateway ─▶ GovernanceGate ─▶ Domain (MCP servers) ─▶ Domain DB
                                          │
                                          └─▶ ACL ─▶ 外部 (mem0 / lvr)
Hermes Runtime ◀── 被 Gateway 呼叫；透過 MCP 呼叫 Domain
```

- 領域層**不**依賴 Hermes 內部結構（只透過 MCP 契約）。
- 外部服務（mem0/lvr）一律經 **ACL**，領域模型不被外部髒概念污染。
- 治理是橫切前置：**任何**進入領域的 command 先過 `GovernanceGate`。

---

## Hermes pin 策略

- production 鎖定特定 commit/tag，**不跟 main**（報告 Part II 風險表：活躍開發 codebase 的 breaking change 是隱形維運稅）。
- 升級走獨立分支 + 回歸測試（LINE 協定 76 測試 + 本 spec BDD）。

---

## 與報告缺口對照（補齊清單）

| 報告 2.4 缺口 | 本架構對應 | 狀態 |
|---|---|---|
| 多租戶/資料隔離不足 | Tenant Edge + Inv-1 + 部署隔離 | 🔴→規格化 |
| 房仲領域工具全缺 | Domain MCP servers（C4/C5/C6/C8/C9） | 🔴→規格化 |
| 領域記憶 schema 缺 | `erm.dbml` 結構化 Requirement | 🔴→規格化 |
| PII 合規未處理 | GovernanceGate + Inv-2/3/8 | 🔴→規格化 |
| LINE 未用 Flex | line-channel.md Flex 卡規格 | 🟡→規格化 |
| 無領域規格 (SDD) | **本 spec kit** + `erm.dbml` + `.feature` | ✅ |
