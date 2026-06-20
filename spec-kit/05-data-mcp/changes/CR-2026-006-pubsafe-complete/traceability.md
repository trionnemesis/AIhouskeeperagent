# Traceability — CR:2026:006 public-safety 完整落地

```
PUBSAFE:TRAFFIC:parse/store  +  MCP:pubsafe:server (traffic cache-backed)
  ├─ Invariant : DI-5（點位入庫，tool 僅回聚合）, Inv-4（occurred_at ROC→ISO）, DI-7
  ├─ Pattern   : DI（conn 注入）
  ├─ Test      : test_ingest.py::TestParseAccidents；test_store.py::TestTrafficAccidents（角點守 haversine）
  ├─ Real-run  : smoke traffic cache-backed（半徑 2/3、無座標）；共用 fetcher 由犯罪真實驗證
  ├─ Mutation  : M5 haversine 失效、M7 跳列 被殺
  └─ Telemetry : ⏳ 事故點數 / 半徑命中

PUBSAFE:CRIME:all  +  DEPLOY:RUN:etl(crime 批次)
  ├─ Invariant : DI-5（鄉鎮市區）, DI-7
  ├─ Test      : test_ingest.py::TestAggregateAll
  ├─ Real-run  : 真實 14200 → 340 groups / 1107 列 / 329 行政區；server query 七堵區→provided
  ├─ Mutation  : M6 只按 county 被殺
  └─ Telemetry : ⏳ 行政區覆蓋率

GOVNET:tls/retry  （重構：自 lvr_mcp.ingest 抽出，CR-005 首版）
  ├─ Invariant : TLS-1（CERT_REQUIRED+check_hostname；僅清 X509_STRICT）
  ├─ Driver    : opdadm.moi.gov.tw 同缺 SKI → 證明跨來源共用
  ├─ Test      : govnet/tests/test_tls.py（TLS 2 + retry 3）
  ├─ Real-run  : plvr + opdadm 兩源安全下載成功
  ├─ Mutation  : M8 不重試 被殺（TLS 變異見 CR-005 M1）
  └─ Telemetry : ⏳ 下載失敗率 / 憑證輪替
```

> 對稱 [CR-2026-005](../CR-2026-005-deploy-hardening/gates.md)：lvr 已 cache-backed；本 CR 完成 public-safety 兩工具 cache-backed，並把 TLS/retry 抽為 `govnet` 共用基建。
