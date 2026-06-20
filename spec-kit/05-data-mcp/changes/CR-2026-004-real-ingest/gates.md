# Gate Checklist — CR:2026:004 real ingest

## GATE:SPEC ✅
- [x] Intent/Delta/Impact/Verification；Stable ID（ETL:lvr:*、ETL:pubsafe:*）；Feature Review；breaking=false

## GATE:RED ✅（實跑）
- [x] parser/aggregate 測試在 stub 上失敗

## GATE:GREEN ✅（實跑）
- [x] parser/roc/aggregate 單元測試通過；既有 22 測試回歸綠

## GATE:VDD ✅（實跑）
- [x] parser deterministic、roc_to_iso 正確、DI fetcher
- [x] **real-run smoke**：真實下載 plvr + 犯罪 CSV → ingest → service（記錄筆數）
- [x] DI-5：public-safety ingest 輸出無點位
- [x] mutation（cp+diff+清 pycache）被殺

## GATE:DEPLOY ✅（由 [CR-2026-005](../CR-2026-005-deploy-hardening/gates.md) 收尾）
- [x] 排程（plvr 每旬 1/11/21）→ `schedule.next_publication_date` + cron
- [x] 新鮮度監控（`is_stale`, DI-9）；download 重試/降級列範圍外（與 Gateway Router 整合）
- [x] 快取落地 erd.dbml 對應表 → `datastore`（lvr_trades/crime_area_stats/provenance）
- [x] plvr TLS 安全修正 → `build_secure_ssl_context`（僅清 X509_STRICT）

## post-Deploy
`telemetry(新鮮度/筆數) → validate → Delta`。
