# Impact Analysis — CR:2026:003 tw-utils ETL

> 治理頁 03 八項。結論：**修改 4 個 lookup（additive，行為不退化）+ 新增 ETL/data；無 breaking change；不觸 Domain invariant 變更 → Feature Review**。

| # | 檢查項 | 結果 |
|---|---|---|
| 1 | Domain invariant 改變 | **否**。受 DI-2/DI-8 約束，無變更 → Feature Review |
| 2 | 資料模型/migration | 新增 `data/*.json`（檔案，非 DB）；無 migration |
| 3 | API contract 破壞 consumer | **否**。lookup 函式簽名不變（postalCode/cityToEnglish/metroLine/bankCode） |
| 4 | UI state / error | 無變更 |
| 5 | BDD scenario | 新增 ETL transform/run 測試；既有不變 |
| 6 | Quality profile | 沿用；ETL 為背景作業非 hot-path |
| 7 | 既有測試失效 | **必須不失效**：data seed = 既有 fixture 值 → 18 測試回歸綠（驗收硬條件） |
| 8 | 監控/告警/Runbook | ETL 排程成功率/資料新鮮度 → 上線後監控（GATE:DEPLOY） |

## 風險

| 風險 | 緩解 |
|---|---|
| 重構 lookup 改讀檔 → 既有行為退化 | data seed 含既有值；既有 18 測試回歸為硬驗收 |
| transform 解析官方格式錯誤 → 錯資料 | transform 純函式 + 以 sample raw 測；DI runner 用 fake fetcher 測 |
| 實際下載需 TDX key/網路 | 下載為 deploy-time；本 CR 只實作可測的 transform/run(DI)，下載 I/O 注入 |

## 裁決
Feature Review → GATE:SPEC。
