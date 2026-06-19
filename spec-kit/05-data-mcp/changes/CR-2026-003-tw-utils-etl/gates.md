# Gate Checklist — CR:2026:003 tw-utils ETL

> 本 CR 同時做 spec + 實作（透過 STDD×VDD 迴圈），故 RED/GREEN/VDD 在本輪實跑。

## GATE:SPEC ✅
- [x] Change Intent / Delta / Impact / Verification Plan
- [x] Stable ID（ETL:tw-utils:*、DATA:tw-utils:*）
- [x] Domain invariant 確認（DI-2/DI-8，Feature Review）
- [x] Breaking change=false

## GATE:RED ✅（實跑）
- [x] etl-transform/etl-run 測試在 stub 上失敗
- [x] 失敗理由 NOT_IMPLEMENTED；斷言業務結果（normalized 輸出）

## GATE:GREEN ✅（實跑）
- [x] etl-transform/etl-run 通過
- [x] **既有 18 測試回歸綠**（lookup 改讀 data 後不退化）
- [x] 未弱化既有測試

## GATE:VDD ✅（實跑）
- [x] transform deterministic
- [x] runner 用注入 fetcher（不真實下載）
- [x] mutation（cp+diff 確認真改檔）被殺
- [x] data 標來源/license（DI-2/DI-8）

## GATE:DEPLOY ⏳（實作 repo / deploy-time）
- [ ] ETL runner 對真實來源排程（TDX key/中華郵政/財金）
- [ ] data 新鮮度監控、ETL 失敗告警
- [ ] rollback（data/*.json 版本化）

## post-Deploy
`production_telemetry(ETL 成功率/新鮮度) → validate → Delta Spec`。
