# 06 · GKE 平台部署規格

> 把既有邏輯架構（[02-spec/system-architecture](../02-spec/system-architecture.md) + [05-data-mcp/architecture](../05-data-mcp/architecture.md)）映射到 **GKE**。架構不變，本區段只規格化「在 GKE 上怎麼跑、怎麼強制不可違背約束」。

## 已確認決策（2026-06-20，使用者拍板）

| 決策 | 採用 | 替代（未選） |
|---|---|---|
| AI Gateway WASM 形態 | **Envoy 專用 egress proxy（proxy-wasm 5 filter）+ NetworkPolicy default-deny** | Cloud Service Mesh / Istio WasmPlugin（規模化再評估） |
| 多租戶隔離 | **Namespace per tenant（單叢集）** | node-pool / cluster per tenant |
| 狀態服務 | **Cloud SQL Postgres + Memorystore Redis**（data MCP 由 SQLite 遷 Cloud SQL） | 叢集內自建 / 混合 |
| 叢集模式 | **GKE Autopilot + 私有叢集 + Cloud NAT** | Standard |

> MVP 先**單租戶**落地（商業 Gate A 未驗證前不鋪多租戶）；namespace-per-tenant 模型確保平滑擴增。`MULTITENANCY_MODE=deployment`、`MEM0_ENABLED=false`（至 Gate B）續用（[configuration](../02-spec/configuration.md)）。

## 檔案

| 檔 | 內容 |
|---|---|
| [`platform-architecture.md`](platform-architecture.md) | 叢集/namespace/工作負載、Envoy egress gateway、網路與安全、不可繞過 egress、不變量→GKE 強制 |
| [`data-and-cicd.md`](data-and-cicd.md) | Cloud SQL/Redis/mem0 store、data MCP 遷移、IaC 佈局、CI/CD+GitOps、可觀測性、SLO/Runbook |
| [`changes/CR-2026-007-gke-deployment/`](changes/CR-2026-007-gke-deployment/) | STDD×VDD Change Package（**GATE:SPEC 本輪**；RED/GREEN/VDD/DEPLOY 為 Phase 3 執行與驗證） |

## 流程（使用者指定三階段）

1. **確認方案** ✅（決策矩陣 + AskUserQuestion 拍板）
2. **更新 spec** ◀ 本輪（CR-2026-007 至 GATE:SPEC）
3. **執行與驗證** ⏳（撰寫完整 IaC/manifests → policy 測試 RED→GREEN→VDD → staging 部署 smoke → prod）
