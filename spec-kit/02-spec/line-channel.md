# LINE 通道規格

> LINE 是唯一觸點。Hermes 單帳號 LINE adapter 生產級（76 測試），但**多租戶並發/重啟/Push 額度未就緒**。本規格補齊邊界。

> ⚠️ **webhook 終結點（MVP 決策，消除雙層矛盾）**：LINE 對單一 channel/URL 只送一次 webhook。MVP 由 **Node Tenant Edge Gateway 終結 webhook**（持有 `LINE_CHANNEL_SECRET`、做 HMAC 驗章 / dedup / 多租戶路由），**Hermes 內建 webhook 入口（:8646）停用**；Hermes adapter 既有的驗章/去重/allowlist 邏輯**作為可複用模組移植到 Node Gateway**，Hermes 僅保留 reply/push 出口。下方「通道現況」描述的是 Hermes 既有單帳號狀態，非 MVP 終結點。

## 通道現況（Hermes 🟢 既有單帳號狀態，報告 2.3）

- 官方 LINE Messaging API，aiohttp 自起 webhook（`/line/webhook` 預設 `:8646`）。
- 安全鏈：body 1 MiB 上限 → HMAC-SHA256 驗章（失敗 401）→ `webhookEventId` 去重 → self-echo 過濾 → 三層 allowlist。
- 計費優化：優先免費 reply token（50s TTL），逾時 fallback 計費 Push。回覆切 ≤5 泡泡 / ≤4500 字。
- 慢回應：>45s 發 Template Buttons，點按用新免費 token 取回快取答案。
- 主動推播：Cron 掛 `LINE_HOME_CHANNEL`。

## 需補齊（🔴/🟡）

| # | 缺口 | 對應 | 處置 |
|---|---|---|---|
| L1 | dedup / reply token in-memory，重啟即失（H2） | Inv-9 | 狀態外移 Redis；`idempotency_key` |
| L2 | 並發 agent run 無 Semaphore（H6） | NFR | per-tenant 並發閘 |
| L3 | 多租戶路由 | Inv-1 | Tenant Edge Gateway：userId→(tenant,seat) |
| L4 | Push 額度監控 | Gate C | 每租戶月 Push 計數 + 告警 |
| L5 | 未用 Flex Message | — | 物件卡/配對卡/HITL 卡用 Flex |
| L6 | webhook tunnel 非開箱即用 | 部署 | named tunnel + TLS；MVP 部署隔離一店一 endpoint |

## 訊息類型與 Flex 卡規格（L5）

| 場景 | 元件 | HITL? |
|---|---|---|
| 物件文案草稿 | Flex bubble + 「核准/編輯/重生成」按鈕 | ✅ 核准前不外流 |
| 帶看說帖 | Flex carousel（機能/交通/學區）+ 來源註腳 | 唯讀 |
| 客戶需求草稿 | Flex bubble（預算/區域/房型）+「確認建檔」按鈕 | ✅ 含 PII 強制 |
| 配對候選 | Flex carousel（標明命中條件）+「通知客戶（需核准）」 | ✅ 對外前 |
| 行情參考 | Flex bubble + **「資料更新至 YYYY-MM」+ 信心分數** 註腳 | 高風險，附聲明 |
| 跟進提醒 | 主動 Push（冪等 key） | — |

## HITL 互動模式（LINE 上的人工核准）

```
AI 產生草稿 → Flex 卡（含草稿 + Approve/Edit/Reject 按鈕）→ 經紀人點按
  ├ Approve → HITLApproved → 執行（建檔/可用文案）
  ├ Edit    → 經紀人改文字 → 視為核准（edited=true）
  └ Reject  → HITLRejected → 中止/重生成
```

> 所有「對外發送給客戶」的訊息，**不直接由 AI 送出**；先送經紀人核准，核准後才由經紀人轉發或系統代發（仍記 audit）。

## 多租戶路由（L3 · Inv-1，Node Gateway）

```
# Node Tenant Edge Gateway（持有 LINE_CHANNEL_SECRET）
on POST /line/webhook:
  1. body ≤ 1 MiB；HMAC-SHA256(body, LINE_CHANNEL_SECRET) 驗章，失敗 → 401   # 驗證點在 Gateway
  2. dedup：Redis SETNX key=`dedup:{webhookEventId}` TTL=10m；已存在 → 跳過（重送冪等）
  3. line_user_id = event.source.userId
  4. (tenant_id, seat_id) = TenantScopeResolver(line_user_id)   # 快取 line_user_id→scope
       ├ 查無綁定 → UnauthorizedAccessBlocked + audit；不進對話
       └ 未 allowlist → SCOPE_NOT_ALLOWLISTED；不進對話
  5. 並發閘：acquire(per-tenant Semaphore)；滿 → CONCURRENCY_LIMITED(排隊)
  6. 注入 ctx → GovernanceGate → Hermes runtime（該 tenant 的 home）
  7. reply：優先免費 reply token（Redis 存 token TTL=50s）；逾時 fallback Push（記 outbound_messages）
```

- **MVP 部署隔離**：一租戶一 endpoint/home，步驟 4 路由表單純（單一 `TENANT_ID`）。
- **應用層多租戶**：共用 endpoint，依綁定分流。

## 冪等與並發（L1/L2 · Inv-9 / REL-2）

- `webhookEventId` 與 reply token 狀態存 Redis（TTL）；重送命中即跳過。
- 推播 `idempotency_key = correlation_id + kind + due_at`（建檔前已決定，避免以 task_id 自我參照）；唯一性以 `(tenant_id, idempotency_key)` 範圍化（見 `follow_up_tasks`）。
- per-tenant Semaphore 限制並發 agent run，上限 `PER_TENANT_MAX_CONCURRENT_RUN`（暫定 **3**），避免突發燒 token/Push；狀態外移 Redis，重啟可恢復（見 [`../03-features/governance-concurrency.feature`](../03-features/governance-concurrency.feature)）。
