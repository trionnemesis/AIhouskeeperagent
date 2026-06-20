# Gate Checklist — CR:2026:007 GKE 部署

## GATE:SPEC ✅（本輪）
- [x] 方案確認（四決策 AskUserQuestion 拍板）
- [x] Intent / Delta / Impact / Verification Plan / Traceability
- [x] Stable ID（DEPLOY:GKE:TOPOLOGY/GATEWAY/NETSEC/STATE/CICD/OBS）
- [x] 設計文件：[platform-architecture](../../platform-architecture.md)、[data-and-cicd](../../data-and-cicd.md)
- [x] breaking=false；spawns CR-2026-008（datastore Postgres backend）

## GATE:RED ✅（Phase 3，本機實跑）
- [x] conftest 對壞 manifest（`:latest` / 非 gateway 開 0.0.0.0/0 / 缺 default-deny / runAsRoot）→ **7 deny 全抓**（[deploy/policy/testdata/bad.yaml](../../../../deploy/policy/testdata/bad.yaml)）

## GATE:GREEN ✅（Phase 3，本機實跑）
- [x] `kustomize build` base + 3 overlays render（34 資源）
- [x] kubeconform **34/34 valid**；conftest base/overlay **0 fail**
- [x] `terraform validate`（google v5）**Success** + `fmt` clean
- [x] CR-2026-008 datastore PG：SQLite 零回歸 + 真實 Postgres 3 測試綠

## GATE:VDD ✅（Phase 3 之 manifest/policy 層，本機實跑）
- [x] 變異 image→`:latest` → conftest 抓（OPS-1）
- [x] 變異 移除 tenant-demo default-deny → conftest 抓（Inv-1）；還原復綠
- [x] CR-008 PG 去 ON CONFLICT → 去重斷言被殺（IntegrityError）
- [ ] **叢集行為**（需真實 GCP）：egress 不可繞過（app 直連失敗/經 gateway 通）、跨租戶隔離、PII egress 遮罩、DI-5 叢集內

## GATE:DEPLOY ⏳（需真實 GCP/GKE — 你的環境）
- [ ] `terraform apply` → build/push images → Secret 注入 → `kustomize|kubectl apply`（或 Config Sync）
- [ ] staging 叢集內 `deploy_smoke.py` + egress/隔離行為驗證 → `@gateB` 綠 → prod 漸進釋出 + 監控

> 本機可驗證的靜態/單元 gate（RED/GREEN/VDD manifest+datastore）已綠；**唯「叢集內行為」與實際 apply 需你的 GCP 專案**（最後一步）。重跑：`bash deploy/verify.sh`。

## 依賴
- CR-2026-008（datastore→Cloud SQL）需於 GATE:GREEN 前就緒（data MCP 多副本）。
- Gate B（`bdd-gate-b.yml`）為 prod / `MEM0_ENABLED` 前置（沿用 [deployment.md](../../../04-roadmap/deployment.md)）。

> **使用者流程定位**：確認方案 ✅ → 更新 spec ✅（本 CR 至 GATE:SPEC）→ 執行與驗證 ⏳（待指示啟動 Phase 3）。
