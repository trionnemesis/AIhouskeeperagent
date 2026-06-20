# Gate Checklist — CR:2026:007 GKE 部署

## GATE:SPEC ✅（本輪）
- [x] 方案確認（四決策 AskUserQuestion 拍板）
- [x] Intent / Delta / Impact / Verification Plan / Traceability
- [x] Stable ID（DEPLOY:GKE:TOPOLOGY/GATEWAY/NETSEC/STATE/CICD/OBS）
- [x] 設計文件：[platform-architecture](../../platform-architecture.md)、[data-and-cicd](../../data-and-cicd.md)
- [x] breaking=false；spawns CR-2026-008（datastore Postgres backend）

## GATE:RED ⏳（Phase 3）
- [ ] conftest 對「開直連 egress / `:latest` / 缺跨租戶 NetworkPolicy」之壞 manifest 失敗（Red Evidence）

## GATE:GREEN ⏳（Phase 3）
- [ ] kubeconform + conftest 全綠；`terraform validate` 通過

## GATE:VDD ⏳（Phase 3）
- [ ] kind/staging：egress 不可繞過（app 直連失敗、經 gateway 通）、跨租戶隔離、PII egress 遮罩、DI-5 叢集內
- [ ] manifest 變異（開 egress / latest / 移 NetworkPolicy）被 policy/行為測試殺

## GATE:DEPLOY ⏳（Phase 3）
- [ ] staging 部署 + `deploy_smoke.py`（叢集內）+ 行為驗證 → `@gateB` 綠 → prod 漸進釋出 + 監控

## 依賴
- CR-2026-008（datastore→Cloud SQL）需於 GATE:GREEN 前就緒（data MCP 多副本）。
- Gate B（`bdd-gate-b.yml`）為 prod / `MEM0_ENABLED` 前置（沿用 [deployment.md](../../../04-roadmap/deployment.md)）。

> **使用者流程定位**：確認方案 ✅ → 更新 spec ✅（本 CR 至 GATE:SPEC）→ 執行與驗證 ⏳（待指示啟動 Phase 3）。
