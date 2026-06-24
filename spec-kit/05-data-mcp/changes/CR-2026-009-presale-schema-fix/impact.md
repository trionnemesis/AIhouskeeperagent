# Impact Analysis — CR:2026:009 預售屋 schema 修正

| # | 檢查 | 結果 |
|---|---|---|
| 1 | Domain invariant 改變 | 否（強化 Inv-5/Inv-6 正確性，非變更語意）→ Feature Review |
| 2 | 資料模型/migration | 無（`lvr_trades` 欄位不變；僅修正寫入值的正確性） |
| 3 | API contract 破壞 | 否（`parse_lvr_csv` 輸出鍵不變；`ingest_lvr` 新增 `building_type` 鍵向後相容） |
| 4 | UI/error | 復用既有 outcome/refused |
| 5 | BDD/test | `test_ingest.py` 改用雙 schema（33/31 欄）真實表頭 fixture；新增預售欄位對齊 + 檔名判別測試 |
| 6 | Quality profile | QP:ETL:BATCH（背景批次；重正確性/冪等） |
| 7 | 既有測試失效 | parse 測試 fixture 由「佔位表頭」升級為真實中文表頭（隨表頭定位調整）；其餘不動 |
| 8 | 監控/Runbook | 可重新開放灌入預售檔（`a_lvr_land_b.csv`）；移除「只灌成屋」之規避 |

## 風險
| 風險 | 緩解 |
|---|---|
| plvr 表頭字串變動（單位「平方公尺/㎡」、括號/斜線） | `_norm_header` 去括號/斜線/單位後 exact match；面積以「建物移轉總面積」不與土地/車位相混；`TestHeaderDrift` 鎖 ㎡/括號/斜線變體可定位 |
| 表頭完全無法辨識 → 既有成屋路徑無聲歸零 | 必填欄缺→回空（拒污染優於猜測）；且 `ingest_lvr` 對「檔在 ZIP 內卻 0 筆」發 `logging.warning`（cron `2>&1`/CI 可偵測），不再靜默；real-run smoke 另比對筆數 |
| 新增 schema（如租賃 _c）佈局再不同 | 表頭動態定位天然涵蓋；類型判別 `building_type_for` 預設成屋（保守） |
| 既有 var/data_mcp.db 已含舊污染預售資料 | 本 CR 僅修 ETL；歷史 db 由「只灌成屋」基線重灌或下旬重抓校正（DI-9） |

裁決：Feature Review → 屬正確性修復（錯價零容忍）。
