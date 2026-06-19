# Impact Analysis — CR:2026:004 real ingest

| # | 檢查 | 結果 |
|---|---|---|
| 1 | Domain invariant 改變 | 否（受 Inv-4/5、DI-5/2/8/9 約束；強化非變更）→ Feature Review |
| 2 | 資料模型/migration | 無（ingest 產 in-memory rows；快取表已於 erd.dbml 規格） |
| 3 | API contract 破壞 | 否（guards/service 介面不變；ingest 為新模組） |
| 4 | UI/error | 復用既有 outcome/refused |
| 5 | BDD/test | 新增 parser/aggregate 單元測試；既有不變 |
| 6 | Quality profile | QP:ETL:BATCH（背景批次） |
| 7 | 既有測試失效 | 否（新模組獨立；guards/service 22 測試不動） |
| 8 | 監控/Runbook | plvr 季更新鮮度、download 失敗告警（GATE:DEPLOY） |

## 風險
| 風險 | 緩解 |
|---|---|
| plvr 含 env-today 之後日期 → 誤判 | TimestampGuard 用真實時鐘正確過濾（已於真實資料驗證）|
| public-safety ingest 引入點位破 DI-5 | 犯罪資料本為區域級；ingest 僅輸出 county/region/category/count，不含座標 |
| download I/O 失敗 | DI fetcher：live 失敗→上層 source_unavailable 降級（REL-4）|
| CSV 編碼/雙表頭解析錯 | parser 純函式 + sample 測試；real-run 驗證 |

裁決：Feature Review → GATE:SPEC。
