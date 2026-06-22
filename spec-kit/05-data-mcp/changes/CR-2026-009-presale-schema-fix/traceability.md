# Traceability — CR:2026:009 預售屋 schema 修正

```
ETL:lvr:header-resolve（表頭動態定位）
  ├─ Invariant : Inv-5（表頭不可辨識→回空，拒污染優於猜測）
  ├─ Pattern   : 表頭名稱定位（取代固定欄索引）— 成屋33欄/預售31欄通用
  ├─ Test      : test_ingest.py TestParseSale（33欄）/ TestParsePresale（31欄對齊+反污染）
  ├─ Real-run  : live a_lvr_land_b.csv → ingest → 松山區單價無極端值
  └─ Mutation  : 面積固定 col15 / 總價固定 col21 / 表頭鍵錯置 → 被殺

ETL:lvr:building-type（檔名判別預售/成屋）
  ├─ Invariant : Inv-6（預售/成屋標註正確）
  ├─ Test      : test_ingest.py TestBuildingType（檔名→類型；交易標的不含「預售」）
  │              + TestIngestDI（_a→成屋、_b→預售，欄位對齊）
  ├─ Consumer  : scripts/etl_run._to_erd_row → building_type 改讀 ingest 標註
  └─ Mutation  : building_type_for 恆回成屋 → 被殺
```

## Bug → 修法 → 證據

| Bug | 根因 | 修法 | RED→GREEN 證據 |
|---|---|---|---|
| 1 預售恆標成屋 | `"預售" in deal_target` 恆 False（交易標的無此字串） | `building_type_for(filename)` 依 `_b/_a` 判別 | `TestBuildingType` 在舊碼 ImportError→修後綠 |
| 2 固定索引錯位 | col15/21/22/25 為成屋 33 欄校準，套 31 欄預售檔錯位 | 中文表頭動態定位 `_build_col_index` | `TestParsePresale` 舊碼讀到 2.0/2000000/0→修後 50.0/3e7/2e6 |
```
