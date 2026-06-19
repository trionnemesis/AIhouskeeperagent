# Traceability — CR:2026:004 real ingest

```
ETL:lvr:parse/roc/ingest
  ├─ Invariant : Inv-4(ROC→ISO→TimestampGuard), Inv-5(不足→refused), DI-2/8/9
  ├─ Pattern   : DI（fetcher 注入）
  ├─ Test      : test_ingest.py（parse_lvr_csv/roc_to_iso on sample；DI fake fetcher）
  ├─ Real-run  : live plvr 115S1 → ingest → query_market（記錄筆數/outcome）
  ├─ Mutation  : roc 偏移、欄位 index 變異被殺
  └─ Telemetry : ⏳ 季更新鮮度

ETL:pubsafe:parse/aggregate/ingest
  ├─ Invariant : DI-5(區域級不引點位), DI-2/8
  ├─ Test      : test_ingest.py（parse_crime_csv/aggregate_crime on sample）
  ├─ Real-run  : live 犯罪 CSV → aggregate → area_crime_stats
  ├─ Mutation  : aggregate 計數/分組變異被殺
  └─ Telemetry : ⏳
```
