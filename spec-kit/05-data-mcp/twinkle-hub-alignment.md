# Twinkle Hub 評估與自建決策（不消費 hosted MCP）

> **拍板（最終）**：**不使用 [hub.twinkleai.tw](https://hub.twinkleai.tw/) 的 hosted MCP**（無 Bearer / 預付 / Alpha SLA 依賴）；**所有 data MCP server 自建**（官方源）；**twtools 的 deterministic 功能以自建 `tw-utils` 重實作**。
> 查證：twtools **無公開可 vendor 之 repo**——[ai-twinkle/Hub](https://github.com/ai-twinkle/Hub) 僅社群回饋、無原始碼，twtools 僅以 hosted MCP（`twtools-*`）暴露（2026-06 查，verified）。故「複用 twtools」= 重實作其功能，而非 vendor 套件或連線。

## 1. Twinkle Hub 是什麼（評估對象）

台灣社群（Twinkle AI）的 **MCP-as-a-Service**：20 個官方 skill（LVR/Transportation/Geo/Healthcare/Education/PCC…）+ 32 個 **twtools** deterministic 工具（中英地址互轉、統編 checksum、捷運路線、公司登記查詢…）+ 53k open-data 目錄。Bearer token、native MCP、每日同步、**Alpha（新註冊暫停、預付）**。

## 2. 決策：自建，不消費 hosted MCP

| # | 原則 |
|---|---|
| 1 | **不連 hub.twinkleai.tw MCP endpoint** — 避免 Alpha / 新註冊暫停 / 預付 / SLA 風險與外部執行期依賴 |
| 2 | **data server 全自建官方源**（plvr / TDX / 各部會 open data / GCIS）— 權威自有 |
| 3 | **twtools 功能自建** — twtools 無公開可 vendor repo（僅 hosted 暴露）→ 以 `tw-utils` **重實作** deterministic 函式（公開演算法 + 官方 open data） |
| 4 | Twinkle 僅作**功能參考 / 介面靈感**，非執行期依賴 |

> 此決策**降低外部依賴與法律/SLA/預付風險**，契合錯價零容忍與自有權威；解除先前「Twinkle 作 fallback」的設計。

## 3. `tw-utils`（自建 deterministic 工具庫）

重實作 twtools 對應的**房仲相關** deterministic 函式（置於 `shared/tw-utils`，可單元測試、無外部執行期依賴）：

| `tw-utils` 函式 | 對應 twtools | 重實作來源 | 用於 |
|---|---|---|---|
| 統編檢查碼驗證 | 統編 checksum | 財政部統一編號檢查碼公開演算法 | `company-registry-mcp` |
| 郵遞區號 / 行政區碼 | 郵遞區號 / 行政區碼 | 中華郵政 open data | `amenities-mcp` geocoding |
| 中英地址互轉 | 中英地址互轉 | 中華郵政地址英譯標準 + open data | `amenities-mcp` |
| 捷運路線 / 站點 | 捷運路線查詢 | **TDX**（已於 amenities-mcp） | `amenities-mcp` transit |
| 銀行代碼 | 銀行代碼 | 財金公司 open data | （加值，後置） |

> 範圍縮限房仲域：只重實作上述房仲相關工具，**不**重做 twtools 全 32 項。

## 4. 對 data server 的影響（取代先前「對齊 + fallback」立場）

| server | 先前（對齊 + Twinkle fallback） | **更新（自建）** |
|---|---|---|
| `lvr-mcp` | Twinkle LVR 作 fallback/交叉比對 | **移除** Twinkle fallback；權威 = 自建 plvr；交叉比對僅用歷史官方資料 |
| `amenities-mcp` | Twinkle Transportation/Geo + twtools 呼叫 | TDX/各部會自建 + **`tw-utils` 自建**（取代 twtools hosted 呼叫） |
| `company-registry-mcp` | twtools 公司登記/統編 + Finance skill | GCIS 自建 + **`tw-utils` 統編驗證**；公司登記走 GCIS（非 twtools hosted） |

## 5. 保留採納的「好慣例」（非因連 Twinkle）

Bearer（ToolAuthZ 簽發）、native MCP **streamable-http**、每日同步檢查、Router 路由——皆為獨立的好設計，沿用；但**不代表連 Twinkle**。

## 6. 治理影響

- **移除** Twinkle 的 `third_party_mcp` 上游 / ACL / 預付配額（不再消費）。
- `tw-utils` 為**自建 library**；provenance authority 依底層資料為 `gov` / `official_api`（TDX / 中華郵政 / 財金），**非 `third_party_mcp`**。
- `third_party_mcp` authority 值保留作未來通用類別，但**本輪無任何 Twinkle hosted 消費**。
- tw-utils 所用 open data（中華郵政/財金/TDX）授權須逐源確認（多為政府資料開放授權第1版，**顯名 DI-2**）。

## 7. Open Questions（更新 / 收斂）

| # | 狀態 | 結論 |
|---|---|---|
| Q8 | **resolved** | 消費 hosted MCP vs 自建 → **自建** |
| Q10 | **resolved** | self-host vs 線上消費 → **不消費**（自建） |
| Q9 | **變更** | twtools 無公開 vendor repo → 改自建 `tw-utils`；須確認所用 open data（中華郵政/財金/TDX）授權與顯名 |

## 8. 決策摘要

> **不連 hub.twinkleai.tw；全自建官方源；twtools 功能以自建 `tw-utils` 重實作（deterministic）。Twinkle 僅功能參考，無外部 hosted MCP 執行期依賴。** 最小化 SLA / 法律 / 預付風險，契合錯價零容忍與自有權威；不改變既有三條硬約束（PII egress / 591-leju 黑名單 / 錯價零容忍）。
