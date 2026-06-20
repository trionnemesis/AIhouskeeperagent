# Gate Checklist — CR:2026:005 部署硬化

## GATE:SPEC ✅
- [x] Intent/Delta/Impact/Verification；Stable ID（DEPLOY:TLS/SCHED/STORE/RUN:*）；breaking=true + migration 記錄

## GATE:RED ✅（實跑）
- [x] 三組測試在 impl 缺席下失敗：schedule `ModuleNotFoundError`、ingest `ImportError(build_secure_ssl_context)`、datastore `ImportError(store)`

## GATE:GREEN ✅（實跑）
- [x] schedule 8、ingest 6（含 TLS 2）、datastore 5 = **19 新測試通過**
- [x] 既有回歸綠（lvr/public-safety 既有 + scope-helper/tw-utils Node）

## GATE:VDD ✅（實跑，cp+diff+清 pycache）
- [x] M1 TLS `check_hostname=False` → 殺 `test_verification_stays_on`
- [x] M2 schedule `> → >=` → 殺 `test_on_publication_day_returns_next`（failures=3）
- [x] M3 store `INSERT OR IGNORE → INSERT` → 殺 `test_dedup_idempotent`
- [x] M4 store 拿掉 provenance → 殺 `test_provenance_recorded_on_upsert`
- [x] 四者還原後全復綠

## GATE:DEPLOY ✅（實跑）
- [x] **plvr 安全 context 真實下載**（無 SSL 錯）→ 5366 解析、去重落地 5266、信義區 365
- [x] **e2e**：落地 → server cache-backed `query_market_tool` 回 `provided n=365`、source 顯名
- [x] **deploy_smoke**（cache-backed）兩 server 啟動、Inv-5（無快取→refused）、DI-5（門牌→refused、聚合無座標）
- [x] **排程**：`next_publication_date`（1/11/21）+ cron `0 6 1,11,21 * *`（見 deployment 文件）
- [x] **新鮮度監控**：`is_stale`（DI-9）
- [x] **快取落地 erd.dbml**：`datastore`（lvr_trades/crime_area_stats/provenance）

## post-Deploy
`telemetry(新鮮度/筆數/refused 率) → validate → Delta`。
未竟（範圍外，已記）：plvr download 重試/斷路器（與 Gateway Router REQ:GW:ROUTER:003 整合）、A1/A2 點位 traffic 落地、犯罪全行政區批次排程。
