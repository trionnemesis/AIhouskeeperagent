# Traceability — CR:2026:005 部署硬化

```
DEPLOY:TLS:context  (build_secure_ssl_context)
  ├─ Invariant : TLS-1（CERT_REQUIRED + check_hostname 恆真；僅清 X509_STRICT）
  ├─ Pattern   : DI（ssl context 注入 live_fetch_plvr）
  ├─ Test      : test_ingest.py::TestSecureContext（verify_mode/check_hostname/旗標）
  ├─ Real-run  : plvr 115S1 安全下載成功（無 SSL 錯）
  ├─ Mutation  : M1 check_hostname=False 被殺
  └─ Telemetry : ⏳ 下載失敗率 / 憑證輪替監控

DEPLOY:SCHED:next/fresh/season  (schedule.py)
  ├─ Invariant : DI-9（短 TTL 重抓校正）
  ├─ Test      : test_schedule.py（旬/月/年交界、發布日當天、新鮮度邊界、季別映射）
  ├─ Deploy    : cron 0 6 1,11,21 * *（deployment 文件）
  ├─ Mutation  : M2 `>=` 被殺
  └─ Telemetry : ⏳ 新鮮度告警

DEPLOY:STORE:schema/lvr/crime/prov  (datastore/store.py)
  ├─ Invariant : DI-5（crime 無座標欄）, DI-7（provenance）, Inv-5（空快取→refused）
  ├─ Pattern   : DI（conn / ingested_at 注入）
  ├─ Test      : test_store.py（upsert/query/dedup/provenance/無座標欄）
  ├─ Real-run  : plvr 落地 5266 + provenance gov；erd 衍生欄 area_ping/unit_price_net
  ├─ Mutation  : M3 去 dedup、M4 去 provenance 被殺
  └─ Telemetry : ⏳ 快取筆數 / 命中率

DEPLOY:RUN:etl/serve  +  MCP:lvr/pubsafe:server (cache-backed) + GATE:DEPLOY:smoke
  ├─ Invariant : Inv-5, DI-5, DI-2（顯名隨快取）
  ├─ Test      : deploy_smoke.py（seed→cache-backed；無快取/門牌→refused；聚合無座標）
  ├─ Real-run  : etl_run lvr → serve query_market_tool 回 provided n=365
  └─ Telemetry : ⏳ refused 率 / 工具延遲
```

> 收尾 [CR-2026-004](../CR-2026-004-real-ingest/gates.md) `GATE:DEPLOY ⏳` 三項（排程 / 新鮮度+重試 / 快取落地）。
