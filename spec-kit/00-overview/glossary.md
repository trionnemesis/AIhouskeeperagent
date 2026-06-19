# 統一語言（Ubiquitous Language）

> DDD 的根基：團隊、程式碼、spec、BDD 場景用**同一套詞**。下表是規範詞彙，程式碼識別子（表名/類別/事件名）以「英文 key」為準。

## 租戶與身分（Tenancy & Identity）

| 中文 | 英文 key | 定義 | 備註 |
|---|---|---|---|
| 經紀業 | `Tenant` (Agency) | 資料隔離**最外層邊界**。所有業務資料屬於唯一 tenant | 隔離不變量的錨點 |
| 店 | `Branch` | 加盟 / 直營 / 自營店 | MVP 可作部署隔離單位（一店一 Hermes home） |
| 經紀人 | `Seat` | 系統使用者，**per-seat 計費單位** | aka Agent in 房仲語境；程式碼識別子用 `Seat`，與「AI Agent」區分 |
| 使用者身分 | `Identity` | LINE userId ↔ 經紀人 的綁定 | allowlist 控管 |

> ⚠️ **命名衝突警告**：「Agent」在房仲語境是「經紀人（人）」，在技術語境是「AI Agent（Hermes runtime）」。本 spec 一律以 **`Seat` / 經紀人** 指人，以 **`Agent Runtime` / Hermes** 指 AI。

## 客戶與物件（Customer & Listing）

| 中文 | 英文 key | 定義 | 備註 |
|---|---|---|---|
| 客戶 | `Customer` | 買方 / 賣方 / 屋主，**PII 邊界** | 含個資，受治理不變量約束 |
| 客戶需求 | `Requirement` | 買方需求：預算 / 區域 / 房型 / 條件 | 結構化，供配對 |
| 物件 | `Listing` | 待售 / 待租物件及其屬性 | owning context = C-Listing |
| 物件建檔 | `ListingProfiled` | 物件建檔完成（配對掃描觸發源） | 對映事件 |
| 物件下架 | `ListingDelisted` | 物件下架，狀態轉移 | 對映事件；狀態機見 governance-state-machines.md |
| 互動 | `Interaction` | 帶看 / 斡旋 / 跟進 等事件 | 時間軸 |
| 跟進任務 | `FollowUpTask` | 排程化的下一步動作 | 由 Cron 主動推播 |

## 內容生成（Content）

| 中文 | 英文 key | 定義 | 備註 |
|---|---|---|---|
| 文案 | `ListingCopy` | 物件標題 / 說明文 | Phase 1 killer，無錯價風險 |
| 說帖 | `ViewingBriefing` | 帶看用機能 / 捷運 / 學區 / 行政區說明 | 即時靜態資料，零延遲 |

## 行情（Market Intelligence）

| 中文 | 英文 key | 定義 | 備註 |
|---|---|---|---|
| 行情參考 | `MarketComp` | 實價登錄彙整的參考價 | **延遲 3–5 月**，輔助用途；報告實測錨點：最新季 115S1(2026 Q1)、最新有效交易日 2026-03-05 |
| 錯價 | `Mispricing` | AI 報出錯誤行情 | **零容忍紅線**，北極星反指標 |
| 配對 | `Match` | 買方需求 × 物件 的結構化比對結果 | Core Domain |

## 治理（Governance）

| 中文 | 英文 key | 定義 | 備註 |
|---|---|---|---|
| 人工核准 | `HITL Approval` | Human-in-the-loop，對外/寫入動作的人工放行閘 | 同時是免責證據 |
| 隔離不變量 | `Isolation Invariant` | 所有查詢硬約束 `WHERE tenant_id=? AND (customer scope)` | 見 invariants.md |
| 稽核軌跡 | `AuditTrail` | append-only 操作 / 查詢記錄 | codebase 原無；映射：聚合=`AuditTrail`／資料表=`audit_logs`／事件=`AuditTrailRecorded` |
| 信心分數 | `ConfidenceScore` | 回答可信度評分，低於閾值觸發拒答/HITL | 行情/高風險查詢用 |
| 拒答 | `Refusal` | 高風險或不確定時主動不回答 | 優於猜測 |
| 資料時間戳防呆 | `TimestampGuard` | 拒絕 `<2010` 或 `>今日+90天` 的資料列 | 過濾 lvr 垃圾值 |
| PII 脫敏 | `PII Redaction` | 身分證 / 財務 / 聯絡資訊的遮蔽 | |

## 對話 Runtime（複用 Hermes）

| 中文 | 英文 key | 定義 | Hermes 模組 |
|---|---|---|---|
| 對話迴圈 | `Conversation Loop` | ReAct 主腦 | `agent/conversation_loop.py` 🟢 |
| 工具註冊 | `Tool Registry` | domain tool 零核心擴充點 | `tools/registry.py` 🟢 |
| 記憶 provider | `Memory Provider` | 長期記憶抽象 | `agent/memory_provider.py` 🟡 |
| 主動推播 | `Cron Push` | 排程主動 LINE 通知 | `cron/scheduler.py` 🟢 |
| Skill | `Skill` | 房仲 SOP / 話術封裝 | `skills/` 🟢 |
