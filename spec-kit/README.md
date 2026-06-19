# 房仲第二大腦 · Spec Kit

> Spec-Driven Development (SDD) 規格包
> 底座：**Hermes-Agent**（pinned）+ **mem0 MCP**（記憶）+ **Node.js**（領域/治理/整合層）
> 互動窗口：**LINE bot**
> 來源依據：Notion《房仲第二大腦：Hermes-Agent 底座可行性與商業化整合報告》(Part I/II/III, 2026-06)

---

## 這份 spec kit 的立場

本規格刻意**繼承來源報告的審查結論，不洗白**。三項硬約束貫穿全部文件：

1. **多租戶 / PII 隔離是 P0 上線 blocker**——不是後補功能。`session_key` 是會話路由 key，**不是**租戶資料邊界。所有資料存取硬約束 `WHERE tenant_id = ?`。
2. **即時行情降級為輔助**——資料延遲 3–5 個月 + 日期解析垃圾值（`MAX=2101`/`MIN=1921`）。行情**不是門面、不是護城河**，需錯價防護才上線。
3. **真護城河 = 結構化客戶記憶 + 配對 + 工作流嵌入**——這是 Core Domain，不是行情。

> ⚠️ 商業案（付費意願）尚未驗證。本 spec kit 是「**怎麼蓋**」的技術契約，不是「**該不該蓋 / 有沒有人付**」的承諾。Go/No-Go gate 見 [`00-overview/north-star-and-gates.md`](00-overview/north-star-and-gates.md)。寫 production code 前，先過商業關卡。

---

## 範圍

- **全域**：8 階段價值鏈的 Bounded Context 地圖（廣度，輕量）
- **深規格**：MVP 垂直切片（深度）
  - **Phase 0**：多租戶 / PII 隔離 + 治理（blocker）
  - **Phase 1**：物件文案 / 帶看說帖生成（第一週 killer，零輸入、零延遲、無錯價風險）
  - **Phase 2**：結構化客戶記憶 + 配對（留存核心 = 護城河）
- **治理**：完整治理規格（獨立 invariants + BDD）

---

## 目錄結構

| 路徑 | 內容 | 對應交付物 |
|---|---|---|
| [`00-overview/`](00-overview/) | 產品願景、統一語言、北極星 KPI 與 Go/No-Go gate | 背景脈絡 |
| [`01-domain/`](01-domain/) | **DDD**：事件風暴地圖、Context Map、聚合、領域事件、治理不變量 | **DDD 事件風暴地圖** |
| [`02-spec/`](02-spec/) | **規格**：系統架構、`erm.dbml`、mem0/LINE/Tool 契約、NFR、錯誤模型、設定清單、狀態機/序列圖 | **spec 文件** |
| [`03-features/`](03-features/) | **BDD**：Gherkin `.feature`（含治理場景）+ cucumber 設定 + step 骨架 | **BDD 行為** |
| [`04-roadmap/`](04-roadmap/) | 分階段 roadmap + Go/No-Go gates + repo 佈局 + 部署步驟 | 落地計畫 |
| [`05-data-mcp/`](05-data-mcp/) | **資料 MCP 層**：資料源決策矩陣 + lvr/amenities/company-registry MCP + AI Gateway 合規層（PII/ToolAuthZ/Policy） | 資料取得層 spec |
| [`.github/workflows/`](.github/workflows/) | Gate B CI（`@gateB` 必綠才接真實資料） | 合規把關 |

### 三大交付物速查

- **DDD 事件風暴地圖** → [`01-domain/event-storming.md`](01-domain/event-storming.md)
- **spec 文件** → [`02-spec/`](02-spec/)（架構 + [`erm.dbml`](02-spec/erm.dbml) + 契約 + NFR）
- **BDD 行為** → [`03-features/*.feature`](03-features/)

---

## 閱讀順序建議

1. [`00-overview/product-vision.md`](00-overview/product-vision.md) — 為什麼這樣設計（含被推翻的假設）
2. [`00-overview/glossary.md`](00-overview/glossary.md) — 統一語言（Ubiquitous Language）
3. [`01-domain/event-storming.md`](01-domain/event-storming.md) — 事件風暴（全貌）
4. [`01-domain/context-map.md`](01-domain/context-map.md) — Bounded Context 邊界
5. [`01-domain/invariants.md`](01-domain/invariants.md) — **治理不變量（必讀，P0）**
6. [`02-spec/system-architecture.md`](02-spec/system-architecture.md) — Hermes + Node.js + mem0 + LINE 架構
7. [`02-spec/erm.dbml`](02-spec/erm.dbml) — 資料模型
8. [`03-features/`](03-features/) — BDD 驗收場景

---

## 慣例

- 語言：繁中 + EN technical terms。
- 標記：`🟢 現成`（Hermes 已具備）· `🟡 需設定/補強` · `🔴 需新增`。
- 事件風暴色票：🟠 Domain Event · 🔵 Command · 🟡 Actor · 🟫 Aggregate · 🟪 Policy · 🟩 Read Model · 🩷 External System · 🟥 Hotspot。
- 所有「估計值」依來源報告標註，須以 POC / 實測驗證。
