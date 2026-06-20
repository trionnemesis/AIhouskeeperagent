# GKE 狀態服務 / IaC / CI-CD / 可觀測性

## 狀態服務（Cloud SQL + Memorystore）

| 服務 | 用途 | 配置 |
|---|---|---|
| **Cloud SQL for PostgreSQL** | domain DB（per-tenant）+ data_mcp 快取（共用）+ mem0 store（pgvector，gated） | 一實例多 DB：`tenant_<id>`（[erm.dbml](../02-spec/erm.dbml)）+ `data_mcp`（[erd.dbml](../05-data-mcp/erd.dbml)）；HA(regional) + PITR 備份 |
| **Memorystore for Redis** | dedup / reply token / 並發閘（Inv-9, REL-1/2） | 標準層 HA；`REDIS_URL` 經 Secret |
| 連線 | Cloud SQL Auth Proxy（sidecar 或 platform ns）+ Workload Identity | 不在 pod 放 DB 帳密；IAM 驗證 |

### data MCP 由 SQLite 遷 Cloud SQL（Phase 3 code CR）

- 現況：[`packages/datastore`](../../packages/datastore) 為 SQLite（CR-005/006）。`erd.dbml` 本即 PostgreSQL、schema 一致。
- 遷移：`datastore.connect` 抽象換 Postgres backend（psycopg/SQLAlchemy）；DDL 由 SQLite 子集對回 erd.dbml；**ETL/查詢介面與測試不變**（store API 穩定）。多副本 data MCP 因此可行（去除 RWO PVC 單副本限制）。
- 列為 **CR-2026-008（datastore Postgres backend）**，於 Phase 3 與 GKE 一起執行驗證。

### audit append-only（SEC-3/Inv-3）
`REVOKE UPDATE, DELETE ON audit_logs FROM app_role;`（或 BEFORE UPDATE/DELETE 觸發器 RAISE）。

### mem0 store
pgvector on Cloud SQL（或託管向量庫）；**`MEM0_ENABLED=false` 至 Gate B**；即使啟用，僅 C5 Mem0Acl 可達（Inv-7）。

## IaC 佈局（規格，Phase 3 撰寫）

```
deploy/
├─ terraform/                 GCP 基礎設施
│   ├─ cluster.tf             Autopilot 私有叢集 + Cloud NAT + 授權網路
│   ├─ cloudsql.tf            Postgres 實例 + DB + 使用者(IAM)
│   ├─ memorystore.tf         Redis
│   ├─ artifact_registry.tf   image repo
│   ├─ iam_wi.tf              Workload Identity 綁定
│   └─ secrets.tf             Secret Manager 條目（值經密管，不入版控）
└─ k8s/                       Kustomize
    ├─ base/                  各元件 base（gateway/data-mcp/hermes/edge/domain-mcp）
    │   └─ networkpolicy/     default-deny + 顯式放行（egress 僅 gateway）
    └─ overlays/
        ├─ staging/           Gate B 驗證環境
        ├─ prod/
        └─ tenant-<id>/       per-tenant（TENANT_ID/HERMES_HOME/LINE secret ref）
```
> Kustomize overlay 管 per-tenant 差異；Terraform 管 GCP 資源。**選 Kustomize 而非 Helm**：overlay 模型直接對應 namespace-per-tenant，less template 魔法。

## CI/CD + GitOps

```
git push → Cloud Build：
  lint/test（Python unittest + Node node:test + BDD）
  → build images（hermes@PINNED_TAG / data-mcp / domain-mcp / fastapi / envoy+wasm）
  → vuln scan（Artifact Analysis）→ push Artifact Registry
  → conftest/kubeconform（manifest policy gate）
GitOps（Config Sync）：reconcile overlays → 叢集
```
- **Gate B 閘**：`.github/workflows/bdd-gate-b.yml` 的 `@gateB` 全綠 → 才允許 sync `prod` overlay / 才評估開 `MEM0_ENABLED`（接真實客戶資料前置，沿用 [deployment.md](../04-roadmap/deployment.md)）。
- Hermes image 由 `HERMES_PINNED_TAG` build，**禁 `:latest`**（OPS-1）；升級走獨立分支 + LINE 協定回歸 + 本 spec BDD。

## 可觀測性（OBS-1~4）

| 面向 | GKE/GCP |
|---|---|
| Metrics | **Managed Service for Prometheus**：每租戶 token/Push 用量、拒答率、HITL 採納率（OBS-1） |
| Logs | **Cloud Logging**：結構化 + correlation_id；Log Router PII scrub（OBS-2/SEC-2） |
| Traces | **Cloud Trace**（OpenTelemetry）：command→event 因果鏈 causation_id（OBS-3） |
| 北極星 | **錯價回報數** dashboard（反指標停損，OBS-4） |
| 成本 | 每租戶月 Push/ token 計數 + 告警（COST-3, Gate C） |

## SLO / Ops

| 項 | 目標 | 機制 |
|---|---|---|
| PERF-2 配對查詢 | < 500ms（hard gate） | Cloud SQL 索引（tenant+budget 複合 / district）；staging 壓測 |
| PERF-1 系統層 p95 | < 10s（hard gate，不含 LLM） | HPA + 並發閘 REL-2 |
| 可用性 | PodDisruptionBudget + regional Cloud SQL | — |
| 慢回應降級 | > 45s → Template Buttons（REL-3） | Hermes 既有 |
| 外部源失效 | 拒答/降級不崩（REL-4） | Router fallback + 斷路器（待 Gateway runtime） |

> Runbook（Phase 3）：發版/回滾（overlay revert）、Hermes 升版、ETL 失敗重跑、Cloud SQL failover、憑證輪替（govnet）。
