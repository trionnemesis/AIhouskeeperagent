# Traceability — CR:2026:008 datastore Postgres 後端

```
STORE:dialect + STORE:pg:*（datastore 雙後端）
  ├─ Spawned-by : CR-2026-007（GKE Cloud SQL → data MCP 多副本）
  ├─ Invariant  : DI-5（crime 無座標欄，跨後端）, DI-7（provenance 一致）
  ├─ Pattern    : DI（connect(url) 選後端）
  ├─ Test       : tests/test_store.py（SQLite 8）、tests/test_store_pg.py（PG 3，DATABASE_URL 注入）
  ├─ Real-run   : docker postgres:16-alpine → lvr 去重/crime DI-5/traffic 半徑 全綠
  ├─ Mutation   : 去 ON CONFLICT → IntegrityError 殺去重斷言
  └─ Telemetry  : ⏳ 連線數 / 快取命中（Cloud SQL）
```

> 對應 erd.dbml（PostgreSQL 為主，SQLite 子集）、[CR-2026-005](../CR-2026-005-deploy-hardening/gates.md)/[CR-2026-006](../CR-2026-006-pubsafe-complete/gates.md)（store API 來源）、[CR-2026-007](../../../06-platform-gke/changes/CR-2026-007-gke-deployment/gates.md)（部署載體）。
