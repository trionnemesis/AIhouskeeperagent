# public-safety-mcp 規格（治安/防詐 · P2）

> 依 **STDD×VDD 治理流程**產出（Change Package：[`changes/CR-2026-001-public-safety/`](changes/CR-2026-001-public-safety/)）。
> Canonical spec；事實只定義一次，他處以 Stable ID 引用。Python FastMCP，獨立進程。

## Stable ID 註冊（本 server 新增）

| Stable ID | 意義 |
|---|---|
| `REQ:PUBSAFE:001` | 交通事故周邊密度（A1/A2，點位聚合非門牌） |
| `REQ:PUBSAFE:002` | 區域治安統計（鄉鎮市區粒度，禁套單一物件） |
| `REQ:PUBSAFE:003` | 防詐查核（165 涉詐網站，無地理粒度，P3） |
| `TOOL:PUBSAFE:001/002/003` | 對應 MCP 工具契約 |
| `UI:PUBSAFE:*` | agent/LINE 回應狀態契約（Loading/Error/Empty/Disabled） |
| `QP:DATA-MCP:READ` | 資料 MCP 讀取品質 Profile（見 [`changes/.../verification-plan.yaml`](changes/CR-2026-001-public-safety/verification-plan.yaml)） |

**引用既有不變量（不重定義）**：`DI-5`(治安粒度封頂，核心)、`DI-2`(顯名)、`DI-3`(時點)、`DI-7`(provenance)、`DI-8`(配額/license)、`Inv-4`(TimestampGuard)、`Inv-5`(拒答優於猜測)。錯誤碼見 [`../02-spec/error-model.md`](../02-spec/error-model.md)。

## 1. 資料源（verified，見 decision-matrix C 區）

| REQ | 來源 | 取得 | 粒度 | 法遵 |
|---|---|---|---|---|
| REQ:PUBSAFE:001 | data.gov.tw 警政署 **A1/A2 交通事故** CSV | 自訂 REST/CSV | **含經緯度點位、不含個資** | 🟢 授權第1版 |
| REQ:PUBSAFE:002 | data.gov.tw **dataset 14200「犯罪資料」** + 各縣市 + 婦幼安全警示 | CSV | **鄉鎮市區/分局級**（刻意降粒度） | 🟢 |
| REQ:PUBSAFE:003 | **165 涉詐網站** CSV（data.gov.tw） | CSV | 無地理 | 🟢 |

> data.gov.tw **非 CKAN**（`/api/3/action` 404）→ 自訂 REST + 各機關 API，逐 dataset 讀 license（DI-8）。勿爬 `ba.npa.gov.tw` 互動查詢。

## 2. MCP Tools

```ts
// REQ:PUBSAFE:001 — 交通事故周邊密度（點位聚合，非個別點/門牌）
traffic_accident_density(ctx, { lat: number, lng: number, radius_m?: number }):
  | { outcome:'provided', density: { grid_cells, total_n, severity_mix },
      time_range: string, source:'內政部警政署', as_of: string }   // DI-2/DI-3
  | { outcome:'refused', reason:'insufficient_data'|'source_unavailable' }
// A1/A2 雖有點位經緯度，輸出一律以「周邊密度聚合」呈現（DI-5），不回個別事故點

// REQ:PUBSAFE:002 — 區域治安統計（鄉鎮市區粒度）
area_crime_stats(ctx, { district: string, category?: string }):
  | { outcome:'provided', stats: { category, count, period }[],
      granularity:'鄉鎮市區', source, as_of, disclaimer }          // DI-5 強制標粒度
  | { outcome:'refused', reason:'insufficient_data'|'source_unavailable' }
// 硬性：禁門牌/點位化、禁「高犯罪/治安差」負面標籤、區域統計禁套單一物件（DI-5）

// REQ:PUBSAFE:003 — 防詐查核（P3，無地理）
fraud_check(ctx, { domain?: string, keyword?: string }):
  { outcome:'provided'|'refused', matches: { value, listed_at }[], source:'165', as_of }
```

## 3. 治理防護鏈（DI-5 為核心）

| 防護 | 規則 | 不變量 |
|---|---|---|
| 粒度封頂 | A1/A2→密度聚合；犯罪資料→鄉鎮市區；**禁門牌/點位精準** | **DI-5** |
| 禁汙名標籤 | Policy 插件攔截「高犯罪/治安差/嫌惡」等對物件的負面標籤 | DI-5 / Policy |
| 禁區域套個體 | 區域統計**不得**呈現為單一物件之精準治安評分 | DI-5 |
| 拒答優於猜測 | 資料粒度不足/來源失效 → `refused` | Inv-5 |
| 時點/顯名 | 必附 time_range/period + 來源機關 | DI-3/DI-2 |
| 日期防呆 | 事故日期套 TimestampGuard | Inv-4 |
| provenance | 標 source/authority='gov'/confidence/as_of 才入庫 | DI-7 |

## 4. UI State Contract（`UI:PUBSAFE:*`，Gate SPEC 要求）

本 server 為 headless MCP，無直接 UI；UI 狀態契約**委派主 spec LINE 層**（[`../02-spec/line-channel.md`](../02-spec/line-channel.md) Flex），對應 agent 回應狀態：

| 狀態 | 對應 |
|---|---|
| Loading | 查詢中（>45s 走慢回應 Template Buttons，REL-3） |
| Error | `source_unavailable` / `SOURCE_QUOTA_EXCEEDED` → 降級訊息（REL-4） |
| Empty | `refused: insufficient_data` → 「資料粒度不足，無法提供」 |
| Disabled | 治安功能未授權角色（ToolAuthZ）/ 該區無足夠資料 |

## 5. 與既有層整合

- 經 **AI Gateway**（PII 非重點—治安資料不含個資；但 Policy 強制 DI-5 中性化；ToolAuthZ 角色控管）。
- 不消費第三方 hosted MCP（延續 Twinkle 決策）；自建官方源。
- 資料表見 [`erd.dbml`](erd.dbml)（`crime_area_stats` / `traffic_accidents` / `fraud_domains`）。

## 6. 驗收（STDD×VDD）

- BDD：[`features/public-safety.feature`](features/public-safety.feature)（含 Red Evidence 要求，GATE:RED）。
- 品質驗證：[`changes/CR-2026-001-public-safety/verification-plan.yaml`](changes/CR-2026-001-public-safety/verification-plan.yaml)（GATE:VDD，QP:DATA-MCP:READ）。
- Gate 狀態：[`changes/CR-2026-001-public-safety/gates.md`](changes/CR-2026-001-public-safety/gates.md)。
- Traceability：[`changes/CR-2026-001-public-safety/traceability.md`](changes/CR-2026-001-public-safety/traceability.md)。
