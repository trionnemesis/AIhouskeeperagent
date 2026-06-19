# Gate Checklist — CR:2026:002 Gateway Router + RAG Adapter

> 5 Gates。spec 階段交付：`GATE:SPEC` ✅；`RED/GREEN/VDD/DEPLOY` ⏳ pending-implementation（條件已定）。

## GATE:SPEC ✅

- [x] Change Intent（[`intent.md`](intent.md)）
- [x] Delta Spec（[`delta.yaml`](delta.yaml)）
- [x] Stable ID 完整（`REQ:GW:ROUTER:*`/`REQ:GW:RAG:*`/`QP:GATEWAY:STANDARD`）
- [x] Domain invariant 已確認（**Domain Review**：Inv-1/Inv-7 執行面強化、未弱化，見 [`impact.md`](impact.md)）
- [x] BDD 可觀察無歧義（[`../../features/gateway-router.feature`](../../features/gateway-router.feature)、[`../../features/gateway-rag.feature`](../../features/gateway-rag.feature)）
- [x] UI states：N/A（Gateway 插件，無 UI；錯誤經既有錯誤碼）
- [x] API contract：插件對既有 tool 簽名透明
- [x] Quality profile 引用（`QP:GATEWAY:STANDARD`）
- [x] Breaking change 已標記（false）

## GATE:RED ⏳

- [ ] 測試在 baseline（無 Router/RAG 實作）失敗
- [ ] Red Evidence 保存
- [ ] 斷言業務結果（越界丟棄/降級/排序），非僅 status
- [ ] Test Agent 未讀實作 diff

## GATE:GREEN ⏳

- [ ] unit/feature/contract 通過；static/lint 通過
- [ ] 實作 Agent 未弱化測試

## GATE:VDD ⏳（契約見 verification-plan.yaml）

- [ ] plugin overhead p95 < 50ms（QP:GATEWAY:STANDARD）
- [ ] Resilience：全源失效→降級不崩、**永不 fallback 到禁用源**；斷路器開/半開
- [ ] **RAG security_domain**：tenant scope 強制（Inv-1）、mem0 ns 校驗（Inv-7）、PII 過濾（DI-1）、authority 排序無 scrape（DI-7/DI-4）— machine-checkable
- [ ] Mutation score ≥ 基線

## GATE:DEPLOY ⏳

- [ ] 無 schema migration（插件無狀態；斷路器狀態於 Redis）
- [ ] Feature flag / controlled rollout
- [ ] Smoke test / Rollback 條件
- [ ] Observability：fallback 率、斷路器觸發、**RAG 越界攔截數（TenantScopeViolationDetected）**
- [ ] Alert 與 Runbook 同步

## post-Deploy

`production_telemetry → validate_quality_assumptions → Delta Spec`（RAG 越界或 fallback 異常 → 觸發新 CR）。
