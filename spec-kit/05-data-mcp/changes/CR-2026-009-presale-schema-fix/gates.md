# Gate Checklist — CR:2026:009 預售屋 schema 修正

## GATE:SPEC ✅
- [x] Intent/Delta/Impact/Verification/Traceability；Stable ID（ETL:lvr:header-resolve / building-type）；breaking=false
- [x] Feature Review：屬資料正確性修復（錯價零容忍），非新功能

## GATE:RED ✅（實跑）
- [x] 新測試在舊碼上失敗：`building_type_for` ImportError；預售欄位以固定索引讀到污染值（2.0 / 2000000 / 0）

## GATE:GREEN ✅（實跑）
- [x] mcp-lvr 25 測試全綠（含成屋33欄無回歸、預售31欄對齊、檔名判別、DI 標註）
- [x] govnet 5 / public-safety 23 回歸綠
- [x] 端到端：`etl_run._to_erd_row` → 松山區=預售、area_ping 對齊、無極端單價

## GATE:VDD ✅（實跑）
- [x] 成屋/預售雙 schema 表頭定位正確；反證固定索引污染值不再出現
- [x] building_type 依檔名（_b=預售/_a=成屋）；交易標的不含「預售」
- [x] mutation（cp+diff+清 pycache）：4 變異（building_type 恆成屋 / 面積固定col15 / 總價固定col21 / 表頭鍵錯置）皆被殺
- [ ] **real-run smoke**：重新灌真實 `a_lvr_land_b.csv` → 比對單價分布（待部署環境執行）

## GATE:DEPLOY（後續）
- [ ] 移除「只灌成屋檔」之規避；ETL 同時灌 `a_lvr_land_a.csv` + `a_lvr_land_b.csv`
- [ ] 歷史 db：以下旬重抓校正（DI-9）或自基線重灌，清除舊污染預售資料
