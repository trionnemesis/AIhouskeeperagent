# Impact Analysis — CR:2026:001 public-safety-mcp

> 治理頁 03 的 8 項必查。結論：**純新增、無 breaking change、無 Domain invariant 變更**（走 Feature Review，非 Domain Review）。

| # | 檢查項 | 結果 |
|---|---|---|
| 1 | Domain invariant 是否改變 | **否**。本 CR 受 `DI-5` 等既有不變量**約束**，未新增/修改/破壞任何不變量 → 走 Feature Review |
| 2 | 資料模型/migration 相容 | **新增**三張獨立表（`crime_area_stats`/`traffic_accidents`/`fraud_domains`），不動既有表 → 向後相容 |
| 3 | API contract 是否破壞既有 consumer | **否**。新增 `TOOL:PUBSAFE:*`，無修改既有 tool |
| 4 | UI state / error handling 是否改變 | UI 委派既有 `line-channel`；error 復用既有錯誤碼（`source_unavailable`/`SOURCE_QUOTA_EXCEEDED`），無新增錯誤碼 |
| 5 | BDD scenario 新增/刪除/衝突 | **新增** `features/public-safety.feature`，與既有 feature 無衝突 |
| 6 | Quality profile 是否仍適用 | 引用既有讀取型 Profile `QP:DATA-MCP:READ`（verification-plan.yaml 定義），與 lvr/amenities 同類 |
| 7 | 既有測試是否因本變更失效 | **否**。新增獨立 feature，未改既有 step/feature |
| 8 | 監控/告警/Runbook 是否需同步 | **是**。新增治安類用量與 DI-5 違規偵測指標 → GATE:DEPLOY 要求更新 dashboard |

## 受影響 Stable ID（由 delta.yaml `affected` 自動列出）

- 不變量：`DI-5`(核心)、`DI-2`、`DI-3`、`DI-7`、`DI-8`、`Inv-4`、`Inv-5`
- 契約：`error-model.md`（復用）、`line-channel.md`（UI 委派）
- Gateway：`Policy`(DI-5 中性化)、`ToolAuthZ`(角色控管)

## 風險（DI-5 為最高）

| 風險 | 緩解 |
|---|---|
| 治安資料被呈現為門牌級精準 → 造假 + 汙名化 | DI-5 硬約束：A1/A2→密度聚合、犯罪→鄉鎮市區；BDD 負向場景驗證 |
| 對物件貼「治安差」負面標籤 → 名譽/房價爭議 | Policy 插件攔截；BDD 場景斷言禁標籤 |
| 區域統計被套用到單一物件 | DI-5；tool 回傳標 granularity，不提供物件級評分 |

## 裁決

走 **Feature Review**（未觸 Domain invariant 變更）→ 進 GATE:SPEC。
