# Impact Analysis — CR:2026:007 GKE 部署

## 觸及範圍（規格層；程式/IaC 為 Phase 3）

| 區 | 影響 | 風險 | 緩解 |
|---|---|---|---|
| 平台架構 | 新增 GKE 拓樸/網路/安全規格 | egress 閘被繞過 | NetworkPolicy egress default-deny + 唯一 Envoy 出口 + Cloud NAT；kind smoke 驗證 |
| 狀態層 | data MCP SQLite→Cloud SQL | 介面/行為漂移 | store API 穩定；erd.dbml 同 schema；拆 CR-2026-008 獨立驗證 |
| 多租戶 | namespace-per-tenant | 跨租戶連通 | NetworkPolicy 跨 ns 零連通 + ResourceQuota；dual-tenant CI（SEC-1/Inv-1） |
| Secret | Secret Manager + WI | 帳密外洩 | 零入版控；IAM 最小權限；Cloud SQL IAM 驗證 |
| CI/CD | GitOps + Gate B 閘 | 未過 Gate B 上 prod | Config Sync 僅在 `@gateB` 綠後 reconcile prod overlay |
| Hermes | 容器化 + pin | 跟到 main / latest | image 鎖 tag；conftest 禁 latest（OPS-1） |

## 不變量交互（落地對應）

- **Inv-1**：namespace + NetworkPolicy + per-tenant Cloud SQL DB；查詢仍 `WHERE tenant_id`。
- **DI-4 / 不可繞過**：egress default-deny；app pod 唯一出向 = Envoy；591/leju Envoy+NAT 雙封。
- **DI-1**：PII WASM 於 Envoy egress（寫 mem0 前）；網路保證流量必經。
- **DI-5**：data MCP 既有護欄（CR-006）於叢集內重驗。
- **SEC-3**：Cloud SQL audit role REVOKE UPDATE/DELETE。
- **Inv-7 / mem0 gating**：`MEM0_ENABLED=false`；僅 C5 Mem0Acl 路徑。

## 相依與順序（Phase 3）

1. Terraform：叢集 / Cloud SQL / Memorystore / NAT / Artifact Registry / WI / Secret Manager。
2. CR-2026-008：datastore Postgres backend（GREEN/VDD）。
3. k8s base + NetworkPolicy + overlays；conftest/kubeconform（RED→GREEN）。
4. staging 部署 → GATE:DEPLOY smoke（叢集內）+ egress/隔離行為驗證（VDD）→ Gate B → prod。

## 回滾
- 規格層：revert 本 CR。
- 部署層（Phase 3）：GitOps overlay revert；Cloud SQL PITR；image tag 回滾。

## 成本（提醒，非阻擋）
- Autopilot per-pod + Cloud SQL(regional HA) + Memorystore + Cloud NAT + Cloud Armor 為固定月成本；MVP 單租戶可最小化（小機型 + 視需要開 HA），與 Gate C unit economics 一併評估。
