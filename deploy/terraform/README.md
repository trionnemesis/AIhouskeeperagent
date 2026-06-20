# deploy/terraform — Hermes 房仲第二大腦 GCP 基礎設施 (IaC)

以 Terraform 規格化（**非 apply**）GKE 平台的 GCP 資源。對應 spec：
[`platform-architecture.md`](../../spec-kit/06-platform-gke/platform-architecture.md)、
[`data-and-cicd.md`](../../spec-kit/06-platform-gke/data-and-cicd.md)、
[`configuration.md`](../../spec-kit/02-spec/configuration.md)。

> Terraform 管 **GCP 資源**；k8s workload / NetworkPolicy 由 `deploy/k8s/` 的 Kustomize overlay 管（per-tenant 差異）。

## 檔案

| 檔案 | 內容 |
|---|---|
| `versions.tf` | terraform `required_version` + google provider (>= 5.x) + GCS backend（佔位，註解） |
| `variables.tf` | `project_id` / `region`(預設 asia-east1) / `zone` / `tenant_ids`(預設 `["tenant-demo"]`) / `env`(staging\|prod) + 共用 labels |
| `network.tf` | VPC + subnet（含 pods/services 次要範圍）+ Private Services Access + Cloud Router + Cloud NAT（集中受控 egress） |
| `cluster.tf` | `google_container_cluster`：Autopilot、私有節點、master 授權網路、release channel REGULAR、Workload Identity |
| `cloudsql.tf` | `POSTGRES_15`、regional HA、backup + PITR、private IP；per-tenant DB `tenant_<id>` + 共用 `data_mcp` + IAM 使用者 |
| `memorystore.tf` | `google_redis_instance`（STANDARD_HA、private、auth + transit encryption） |
| `artifact_registry.tf` | `google_artifact_registry_repository`（docker, `hermes`） |
| `iam_wi.tf` | 各 ns KSA→GSA Workload Identity 綁定 + 最小權限（Cloud SQL Client/Instance User、Secret Accessor） |
| `secrets.tf` | `google_secret_manager_secret` 容器（LINE / DB / Redis / 模型路由）；**值不入版控**，經密管注入 |
| `outputs.tf` | cluster name/endpoint、Cloud SQL connection name、registry url、GSA emails |

## 用法

```bash
cd deploy/terraform

# 1) 先建立 GCS state bucket（chicken-egg，不由本 stack 管），再啟用 versions.tf 的 backend 區塊：
#    gsutil mb -l asia-east1 gs://hermes-tfstate-<project>
#    gsutil versioning set on gs://hermes-tfstate-<project>

terraform init       # 下載 provider；啟用 backend 後初始化遠端 state
terraform plan  -var="project_id=YOUR_PROJECT" -var="env=staging"
terraform apply -var="project_id=YOUR_PROJECT" -var="env=staging"
```

建議以 `*.tfvars`（不入版控）或 CI 變數帶 `project_id` 等：

```hcl
# staging.tfvars（範例；勿提交真值）
project_id              = "your-gcp-project"
env                     = "staging"
region                  = "asia-east1"
tenant_ids              = ["tenant-demo"]
master_authorized_cidrs = [
  { cidr_block = "203.0.113.0/24", display_name = "ops-vpn" },
]
```

```bash
terraform plan -var-file=staging.tfvars
```

## State 後端

- 預設 **local state**（`versions.tf` 的 `backend "gcs"` 為註解佔位）。
- 上線前務必改用 **GCS backend**（remote state + locking + versioning）。bucket 須先存在。

## 變數

| 變數 | 預設 | 說明 |
|---|---|---|
| `project_id` | （必填） | GCP project id |
| `region` | `asia-east1` | 主要 region（資料落地境內） |
| `zone` | `asia-east1-a` | provider 預設 zone（regional 資源不依賴） |
| `env` | `staging` | `staging` \| `prod`；影響命名、labels、deletion_protection |
| `tenant_ids` | `["tenant-demo"]` | 每租戶建立 `tenant_<id>` DB |
| `master_authorized_cidrs` | `[]` | kube-API 控制面授權網路（維運/Cloud Build）；佈署前須補 |
| `cloudsql_tier` | `db-custom-2-7680` | Cloud SQL 機型 |
| `cluster_name` | `hermes` | 資源命名前綴 |

## 與 spec 對應（驗收綁定）

| spec 約束 | 本 IaC 落地 |
|---|---|
| Autopilot + 私有叢集 + Cloud NAT | `cluster.tf`（`enable_autopilot`、`private_cluster_config`）+ `network.tf`（Cloud NAT） |
| DI-4 集中受控 egress | Cloud NAT 為唯一對外路徑；egress default-deny / Envoy 唯一出口由 `deploy/k8s` NetworkPolicy 補強 |
| 租戶隔離（Inv-1） | per-tenant DB `tenant_<id>`（`cloudsql.tf`）；namespace + NetworkPolicy 於 k8s 層 |
| 狀態服務 | Cloud SQL Postgres（regional HA + PITR）+ Memorystore Redis（STANDARD_HA） |
| Secret 零入版控（SEC-2） | `secrets.tf` 僅建容器，無 `secret_version`；值經密管注入 |
| Workload Identity 最小權限 | `iam_wi.tf`：KSA→GSA + Cloud SQL Client / Secret Accessor |
| image 來源 / OPS-1 | Artifact Registry `hermes` repo；tag pin、禁 `:latest`（CI 強制） |

## 注意

- 本 stack **不含任何 secret 值**；`google_secret_manager_secret_version` 刻意未建立。
- `deletion_protection` 於 `env="prod"` 對 GKE 與 Cloud SQL 自動開啟。
- Cloud SQL / Redis 採 Private Services Access，須等 `google_service_networking_connection` 建立完成（已以 `depends_on` 表達）。
