# amenities-mcp 規格（設施/交通/座標 · P1）

> 生活機能與帶看說帖的資料層。混合 TDX OAuth API + open-data CSV ETL + geocoding pipeline。Python FastMCP，獨立進程。

## 1. 資料源（verified 除另註）

| 子域 | 來源 | 取得 | 頻率/限制 | 授權 |
|---|---|---|---|---|
| 交通站點 | **TDX** 運輸資料流通服務 | OAuth2 client_credentials（token 1天），JSON/GeoJSON 帶 `PositionLat/Lon` | 2024/1 起收費要點 + 速率限制（未註冊~50次/日）；*per-second 速率與政府/公益折扣 unverified，待查 TDX 收費要點（Q3）* | 註冊制 |
| 學校 | 教育部 data.gov.tw **6087** | CSV 批次 | 每學年 | 開放 |
| 醫療院所 | 健保署 **39283** | CSV 批次 | 每日 | 開放 |
| 超商 | 商業署（5大超商） | CSV 批次 | 每月 | 開放 |
| 嫌惡設施 | 跨機關拼湊（內政部/台電/能源署/NCC/宗教資訊）+ OSM Overpass | CSV + 自架 Overpass | 各源不一 / OSM 即時 | OSM=ODbL（署名+share-alike） |
| geocoding | **TGOS** 全國門牌定位（主）+ NLSC（備） | 批次 API | TGOS 每日額度 **unverified**（Q2）；Lite 免申請，全國門牌定位限政府/法人/學術/產業 | — |

> ⚠️ **學校/醫院/超商名錄皆 address-only 無經緯度**（verified）→ 必須自建 geocoding pipeline。
> ⚠️ **data.gov.tw 非 CKAN**（`/api/3/action` 回 404）→ 用自訂 REST（`/api/v1/rest/dataset`、`/datasets/export/csv`）+ 各機關來源 API；**逐 dataset 驗證 endpoint**，不可假設統一（Q7）。
> ♻️ **自建 `tw-utils`（重實作 twtools 功能，非連 hosted）**：中英地址互轉/郵遞區號/行政區碼（中華郵政 open data）、捷運路線（TDX）；deterministic、防幻覺、無外部執行期依賴。精準座標仍以 TGOS 為權威。**不消費** Twinkle hosted MCP（見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md)）。

## 2. MCP Tools

```ts
// 周邊交通（捷運/台鐵/高鐵/輕軌/公車）
nearby_transit(ctx, { lat: number, lng: number, radius_m?: number, modes?: string[] }):
  { stations: { name, mode, lat, lng, distance_m }[], source: 'TDX', as_of }
// 自動換 TDX token middleware；遵 TDX 速率(DI-8)

// 周邊生活機能（學校/醫院/超商）
nearby_facility(ctx, { lat: number, lng: number, type: 'school'|'hospital'|'convenience', radius_m? }):
  { facilities: { name, type, address, lat?, lng?, distance_m?, geocode_confidence }[], source, as_of }

// 周邊嫌惡設施（中性呈現）
nearby_disamenity(ctx, { lat, lng, radius_m? }):
  { items: { kind, name?, distance_m, source, as_of }[], note: '中性描述，不代表房價影響判斷' }
// Policy 強制中性用語、附來源+時點、禁絕對化標籤(DI-5 精神)

// 地址→座標（內部主要供上述定位，也可獨立呼叫）
geocode(ctx, { address: string }):
  | { outcome:'provided', lat, lng, confidence, source: 'TGOS'|'NLSC' }
  | { outcome:'refused', reason: 'low_confidence'|'not_found' }      // DI-6：低信心不輸出精準座標
```

## 3. ETL / Geocoding pipeline

```
open-data CSV (學校每學年 / 醫療每日 / 超商每月)
  → 排程 ETL 入庫（逐 dataset 讀 license 欄位，DI-8）
  → 地址正規化 → geocode(TGOS 主→NLSC 備→快取)
  → 信心分數標記；低信心不入「精準座標」欄（DI-6）
  → 標 provenance {source, authority, confidence, as_of}（DI-7）
TDX：即時 API + token 快取（1天），不入庫長存（站點定期更新）
OSM Overpass：自架，ODbL 署名；嫌惡設施補座標
```

## 4. 治理對應

| 規則 | 不變量 |
|---|---|
| 低信心 geocoding 不輸出精準座標 | DI-6 |
| 嫌惡設施中性化、附來源時點、禁絕對化 | DI-5（精神）/Policy |
| 各源 rate-limit/授權遵守，逐 dataset 讀 license | DI-8 |
| provenance 必附才入 mem0 | DI-7 |
| 來源顯名（OSM ODbL/政府機關） | DI-2 |
| 外部源失效降級不崩 | REL-4 |

## 5. 成本/額度 open questions

- TDX 2024/1 收費下查詢量落免費或付費層（Q3）→ 須估 `nearby_transit` 呼叫量。
- TGOS 每日 geocoding 額度具體數字 unverified（Q2）→ 影響是否需 NLSC 備援/自建 geocoder。

## 6. 與帶看說帖（主 spec C4）對接

`amenities-mcp` 的輸出餵主 spec [`../01-domain/`](../01-domain/) 的 `ViewingBriefingGenerated`（帶看說帖），其 `sources[]`（Inv-6a 外部資料溯源）即由本 server 的 provenance 產生。

## 7. 驗收

見 [`features/amenities-geocoding.feature`](features/amenities-geocoding.feature)。
