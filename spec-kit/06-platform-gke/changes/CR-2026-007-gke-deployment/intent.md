# Change Intent — CR:2026:007 GKE 部署規格

> STDD×VDD Change Package。把既有邏輯架構部署到 GKE。**本輪止於 GATE:SPEC**（使用者流程：確認方案 → 更新 spec → 執行驗證）。

## Change Intent

在 **GKE Autopilot + 私有叢集 + Cloud NAT** 上落地系統，強制所有不可違背約束（Inv-1 / DI-1/4/5 / SEC-3/4 / OPS-1 / mem0 gating）。已拍板四決策見 [README](../../README.md)。

範圍（規格化，非本輪執行）：
- **DEPLOY:GKE:TOPOLOGY** — namespace-per-tenant + 共用 data-mcp/gateway/platform ns；工作負載 kind 對照。
- **DEPLOY:GKE:GATEWAY** — Envoy egress proxy（proxy-wasm 5 filter）為唯一不可繞過出口 + NetworkPolicy egress default-deny。
- **DEPLOY:GKE:NETSEC** — 私有叢集/Cloud NAT、591·leju 封鎖、Cloud Armor、Workload Identity + Secret Manager、Pod 安全。
- **DEPLOY:GKE:STATE** — Cloud SQL Postgres（domain per-tenant + data_mcp 共用）+ Memorystore Redis；data MCP 由 SQLite 遷 Cloud SQL（拆 CR-2026-008）。
- **DEPLOY:GKE:CICD** — Artifact Registry + Cloud Build + Config Sync GitOps + Kustomize overlay；Gate B 閘。
- **DEPLOY:GKE:OBS** — Managed Prometheus / Cloud Logging(PII scrub) / Cloud Trace / 北極星 dashboard。

## 邊界（STDD 硬約束）

- **架構不變**：僅規格化 GKE 實現，不改邏輯架構（02-spec / 05-data-mcp）。
- **不可繞過 egress** 為硬需求：NetworkPolicy default-deny + 唯一 Envoy 出口，非僅靠 Gateway 內部邏輯。
- **Hermes pin 不變**（OPS-1）；image 禁 `:latest`。
- **mem0 gating 不變**：`MEM0_ENABLED=false` 至 Gate B。
- MVP 先單租戶；namespace 模型保留多租戶擴增。
- 「測試」對 infra = manifest policy（conftest/kubeconform）+ kind/staging 行為驗證（egress 封鎖、跨租戶隔離）。

## Definition of Ready
- [x] 方案決策已確認（AskUserQuestion 拍板四項）
- [x] Intent / Delta / Impact / Verification Plan（GATE:SPEC 產物）
- [ ] RED/GREEN/VDD/DEPLOY — Phase 3（執行與驗證）
