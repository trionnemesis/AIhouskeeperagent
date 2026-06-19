# Gate Checklist — CR:2026:001 public-safety-mcp

> 5 Gates（治理頁 07）：`GATE:SPEC → RED → GREEN → VDD → DEPLOY`。
> 本 CR 為 **spec 階段**交付：`GATE:SPEC` 可現在判定；`RED/GREEN/VDD/DEPLOY` 待實作期執行（狀態：⏳ pending-implementation，已預先定義通過條件）。

## GATE:SPEC ✅（本階段可判定）

- [x] Change Intent 清楚（[`intent.md`](intent.md)）
- [x] Delta Spec 已建立（[`delta.yaml`](delta.yaml)）
- [x] Stable ID 完整（REQ/TOOL/UI/DATA:PUBSAFE:* + affected 既有 ID）
- [x] Domain invariant 已確認（受 `DI-5` 等約束，無變更 → Feature Review，見 [`impact.md`](impact.md)）
- [x] BDD scenario 可觀察且無歧義（[`../../features/public-safety.feature`](../../features/public-safety.feature)）
- [x] UI states 已涵蓋 Loading/Error/Empty/Disabled（`UI:PUBSAFE:*`，委派 line-channel；見 public-safety-mcp.md §4）
- [x] API contract 已定義（`TOOL:PUBSAFE:001/002/003`）
- [x] Quality profile 已引用（`QP:DATA-MCP:READ`，[`verification-plan.yaml`](verification-plan.yaml)）
- [x] Breaking change 已標記（delta.yaml `breaking_change: false`）

## GATE:RED ⏳（實作期；通過條件已定）

- [ ] 新測試在 baseline（無 public-safety 實作）上**失敗**（`test_fails_on_baseline`）
- [ ] Failure reason 與 REQ:PUBSAFE:* 一致
- [ ] Red Evidence 保存（requirement_id / test_name / baseline_commit_sha / failure_message / failure_location / timestamp）
- [ ] 測試未 Mock 整個 SUT、不只驗 status code（斷言 DI-5 粒度/拒答業務結果）
- [ ] Test Agent 未讀實作 diff（權限隔離，頁 06）

## GATE:GREEN ⏳（實作期）

- [ ] unit / feature_acceptance / contract 測試通過
- [ ] static analysis / lint 通過
- [ ] 實作 Agent 未弱化/刪除/skip 測試（`protected_tests_unmodified`）

## GATE:VDD ⏳（實作期；契約見 verification-plan.yaml）

- [ ] Mutation score ≥ 基線（治安粒度/拒答邏輯高標）
- [ ] Performance budget（QP:DATA-MCP:READ p95 < 800ms）通過
- [ ] Resilience：source_unavailable/quota/timeout → 降級 refused 不崩（REL-4）
- [ ] Security scan 通過或核准例外
- [ ] **DI-5 domain assertions**：無門牌/點位輸出、無負面標籤、區域統計不套物件（machine-checkable）

## GATE:DEPLOY ⏳（實作期）

- [ ] Migration 可回復/向後相容（三新表，純新增）
- [ ] Feature flag / controlled rollout
- [ ] Smoke test
- [ ] Rollback 條件
- [ ] Observability dashboard 更新（治安用量 + **DI-5 違規計數**）
- [ ] Alert 與 Runbook 同步

## post-Deploy

`production_telemetry → validate_quality_assumptions → Delta Spec`（DI-5 違規或錯資訊回報 → 觸發新 CR；對齊主 spec 北極星反指標）。
