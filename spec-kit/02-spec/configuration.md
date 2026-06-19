# 集中設定 / Secret / Feature Flag 清單

> 補散落各檔的設定缺口。每項註明：當前值/預設、是否已決、對應 Inv/NFR。`已決=否` 者須在對應 Phase 前定值。

## Feature Flags

| flag | 預設 | 已決 | 說明 | 對應 |
|---|---|---|---|---|
| `MEM0_ENABLED` | `false` | ✅ | Gate B 通過才可開 | Inv-7, OPS-3 |
| `MULTITENANCY_MODE` | `deployment` | ✅ | `deployment`（一店一 home）/ `app_level` | 架構 §部署隔離 |

## LINE 通道（Secret）

| 變數 | 已決 | 說明 | 對應 |
|---|---|---|---|
| `LINE_CHANNEL_SECRET` | ✅ | HMAC-SHA256 驗章（**終結於 Node Gateway**） | SEC-4, line-channel |
| `LINE_CHANNEL_ACCESS_TOKEN` | ✅ | reply/push 出口 | line-channel |
| `LINE_HOME_CHANNEL` | ✅ | Cron 主動推播目標 | C9 |
| `LINE_PUSH_MONTHLY_QUOTA` | ❌ 待定 | 每租戶月 Push 上限（告警閾值） | COST-3 |

> ⚠️ Secret 一律不入版控；經密管（vault/環境注入）。本清單僅列**名稱與用途**，非值。

## 資料層

| 變數 | 預設 | 說明 | 對應 |
|---|---|---|---|
| `DATABASE_URL` | — | Postgres（prod） | 架構 |
| `SQLITE_PATH` | `./dev.db` | dev | 架構 |
| `REDIS_URL` | — | dedup / reply token / 冪等 / 並發閘狀態 | Inv-9, REL-1/2 |
| `TENANT_ID` | — | 部署隔離下綁定單一租戶 | Inv-1, OPS-2 |

## 可調閾值（已決/待測）

| 變數 | 建議值 | 已決 | 說明 | 對應 |
|---|---|---|---|---|
| `MARKET_CONFIDENCE_THRESHOLD` | ❌ 待 POC | 否 | 低於即 `MarketCompRefused(low_confidence)` | Inv-5 |
| `TIMESTAMP_GUARD_LOWER` | `2010-01-01` | ✅ | 行情列下界 | Inv-4 |
| `TIMESTAMP_GUARD_UPPER_DAYS` | `90` | ✅ | 今日+N 天上界（濾 2101/2033） | Inv-4 |
| `ITERATION_BUDGET` | `8000` | 🟡 暫定 | 每 session token/iteration 上限，超限回最佳草稿 | COST-1 |
| `PER_TENANT_MAX_CONCURRENT_RUN` | `3` | 🟡 暫定 | per-tenant 並發閘上限 | REL-2 |
| `HITL_PENDING_TIMEOUT_HOURS` | `72` | 🟡 暫定 | Pending 逾時自動駁回 | Inv-2 |
| `REPLY_TOKEN_TTL_SEC` | `50` | ✅（LINE 固定） | reply token 有效期 | line-channel |
| `SLOW_RESPONSE_THRESHOLD_SEC` | `45` | ✅ | 慢回應降級觸發 | REL-3, PERF-1 |
| `DATA_RETENTION_DAYS` | ❌ 待法務 | 否 | 各表保留期 | Inv-10 |

## 模型路由 / 外部服務

| 變數 | 說明 | 對應 |
|---|---|---|
| `OPENROUTER_API_KEY`（或各 provider key） | 分層路由統一入口 | COST-2 |
| 模型路由表：`MODEL_FAST`（查詢/文案）/`MODEL_STRONG`（議價/說帖）/`MODEL_LOCAL`（PII, Qwen/Ollama） | 分層守毛利 | COST-2, SEC-6 |
| `GROQ_API_KEY` | STT whisper-large-v3-turbo | C3 |
| `HERMES_PINNED_TAG` | Hermes 鎖定版本（不跟 main） | OPS-1 |
| `HERMES_HOME` | per-tenant home（部署隔離） | OPS-2 |
