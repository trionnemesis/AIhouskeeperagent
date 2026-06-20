# Gate Checklist — CR:2026:008 datastore Postgres 後端

## GATE:SPEC ✅
- [x] Intent/Delta/Impact/Verification；Stable ID（STORE:dialect/pg:*）；spawned_by CR-007；breaking=false

## GATE:RED ✅（實跑）
- [x] test_store_pg 在無 PG 支援時失敗（連線/dialect 未實作）

## GATE:GREEN ✅（實跑）
- [x] SQLite 零回歸：datastore 8 測試 + deploy_smoke + lvr/crime e2e 全綠
- [x] 真實 Postgres（docker postgres:16-alpine + DATABASE_URL）：3 PG 測試綠
  - lvr 去重/查詢/provenance（ON CONFLICT DO NOTHING、%s 佔位、dict_row）
  - crime DI-5（information_schema 無 lat/lng）
  - traffic 半徑 bbox+haversine 跨後端一致

## GATE:VDD ✅（實跑，cp+diff）
- [x] PG 去掉 ON CONFLICT → 第二次 upsert 觸 UNIQUE IntegrityError → 殺去重斷言；還原復綠

## GATE:DEPLOY ⏳（與 CR-007 一起，需真實 GCP）
- [ ] Cloud SQL 起 + `DATA_MCP_DB=postgresql://...` → data MCP 多副本（叢集內 smoke）
- [ ] CI 起 postgres service 跑 test_store_pg

> 依賴：`psycopg[binary]`（requirements.txt）；SQLite 路徑零額外依賴。
