# Traceability — CR:2026:003 tw-utils ETL

```
ETL:tw-utils:transform / run / load
  ├─ Domain Invariant : DI-2(顯名), DI-8(逐源 license)
  ├─ Pattern          : DI（runner 注入 fetcher）
  ├─ BDD/Test         : test/etl-transform.test.ts（純 transform）、test/etl-run.test.ts（DI fake fetcher）
  ├─ Data             : data/{postal,bank,city-en,metro}.json（seed→ETL 產出全量）
  ├─ Regression       : test/{postal,address,metro,bank}.test.ts（既有 18，改讀 data 後須綠）
  ├─ Red Evidence     : stub NOT_IMPLEMENTED 失敗
  ├─ Mutation         : transform 解析常數/key 變異被殺（cp+diff）
  ├─ Quality Verify   : QP:ETL:BATCH（deterministic/idempotent）
  └─ Production Telemetry : ⏳ ETL 排程成功率/資料新鮮度
```
