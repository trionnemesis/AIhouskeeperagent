# @hermes-re/tw-utils

> 自建 deterministic 台灣工具庫（**重實作 twtools 功能，不連 hub.twinkleai.tw hosted MCP**）。
> Spec 追溯：[`spec-kit/05-data-mcp/twinkle-hub-alignment.md`](../../spec-kit/05-data-mcp/twinkle-hub-alignment.md) §3。
> 零執行期依賴；以 Node 22+ 內建 `node:test` + TS type-stripping 執行（無需 npm install）。

## 已實作（loop engineering 首批）

| 函式 | 追溯 spec | 說明 |
|---|---|---|
| `validateUbn(ubn)` | [`company-registry-mcp.md`](../../spec-kit/05-data-mcp/company-registry-mcp.md) | 統一編號檢查碼（含第7碼為7特例） |
| `rocYearToGregorian(y)` / `parseRocSeason(s)` | [`lvr-mcp.md`](../../spec-kit/05-data-mcp/lvr-mcp.md) | 民國↔西元、民國季解析（115S1→2026Q1） |

## 執行

```bash
node --test test/*.test.ts      # Node 22+，零依賴
```

## STDD×VDD loop log（本次 loop engineering 證據）

依治理頁 07 的 `GATE:RED → GREEN → VDD`，逐函式跑微迴圈：

| 迭代 | 元件 | GATE:RED（stub 失敗） | GATE:GREEN（實作通過） | GATE:VDD（mutation） |
|---|---|---|---|---|
| 1 | `validateUbn` | ✅ 4/4 fail（`NOT_IMPLEMENTED`，理由符需求） | ✅ 4/4 pass | ✅ `%5→%4` 變異被殺 |
| 2 | `roc-date` | ✅ 3/3 fail | ✅ 3/3 pass | ✅ `+1911→+1912` 變異被殺 |
| — | 全套件 regression | — | ✅ **7/7 pass** | 還原後全綠 |

- **Red Evidence**：測試在 baseline（stub）確實失敗、失敗理由與需求一致、未 mock SUT、斷言業務結果（非僅 status）——符合治理頁 06。
- **Mutation**：人工注入變異（`%5→%4`、`+1911→+1912`）皆被測試殺死，證明非弱測試；還原後 7/7。
- 測試向量為**手算**，未複製 production 演算法到測試（防自證式測試）。

## 資料 ETL（CR-2026-003）

`postalCode`/`cityToEnglish`/`metroLine`/`bankCode` 已改由 **ETL 載入** `data/*.json`（seed 先行，完整資料由 ETL 對官方來源產出）：
- `etl/transform.ts`：純 transform（raw→normalized），STDD×VDD 可測核心。
- `etl/run.ts`：**DI'd runner**（注入 fetcher；實際下載為 deploy-time）。
- `etl/sources.ts`：官方來源 + 顯名/授權（DI-2/DI-8）。
- `etl/load.ts` + `data/{postal,bank,city-en,metro}.json`。

全套件 **24/24**（含既有 lookup 回歸 + ETL transform/run）。完整資料下載（中華郵政/TDX/財金）為 deploy-time I/O，由注入的 fetcher 提供。
