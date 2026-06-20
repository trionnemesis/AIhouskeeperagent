# deploy/ — GKE 部署落地（CR-2026-007 / CR-2026-008 Phase 3）

> 規格見 [`spec-kit/06-platform-gke/`](../spec-kit/06-platform-gke/)。本目錄為**可驗證的 IaC + manifests + policy gate**。實際 apply 到 GCP/GKE 需你的專案與憑證（最後一步）。

```
deploy/
├─ terraform/   GCP 基礎設施（Autopilot 私有叢集 / Cloud SQL / Memorystore / NAT / WI / Secret Manager）
├─ k8s/         Kustomize：base/（含 networkpolicy 安全核心）+ overlays/{staging,prod,tenant-demo}
├─ policy/      conftest(Rego v1) 合規 gate：OPS-1 image pin / DI-4 egress / Pod 安全 / Inv-1 default-deny
└─ verify.sh    一鍵跑本機可驗證的 gate（kustomize + kubeconform + conftest）
```

## 本機已驗證（Phase 3，無需 GCP）

| Gate | 工具 | 結果 |
|---|---|---|
| Terraform 靜態 | `terraform validate`（google v5） | ✅ Success + `fmt` clean |
| k8s render | `kustomize build`（base + 3 overlays） | ✅ 34 資源 |
| schema | kubeconform | ✅ 34/34 valid |
| policy RED | conftest（故意壞 manifest） | ✅ 7 deny 全抓 |
| policy GREEN | conftest（真實 base/overlay） | ✅ 0 fail |
| policy VDD | 變異 image→latest / 移 default-deny | ✅ 各被抓、還原復綠 |
| datastore PG | docker postgres:16 + DATABASE_URL | ✅ 3 PG 測試（CR-008） |

## 執行（本機 gate）

```bash
bash deploy/verify.sh           # kustomize + kubeconform + conftest（需 docker）
# datastore PG（需 docker）：
docker run -d --rm --name pg -e POSTGRES_PASSWORD=pg -e POSTGRES_DB=data_mcp -p 55432:5432 postgres:16-alpine
DATABASE_URL=postgresql://postgres:pg@127.0.0.1:55432/data_mcp \
  .venv/bin/python -m unittest discover -s packages/datastore/tests
```

## 部署到 GCP（需你的環境，尚未執行）

1. `cd deploy/terraform && terraform init && terraform apply`（先設 `project_id`、建 GCS state bucket、補 `master_authorized_cidrs`）。
2. build/push images 至 Artifact Registry（Hermes 鎖 `HERMES_PINNED_TAG`，禁 `:latest`）。
3. 經 Secret Manager + External Secrets 注入 secret（LINE/DB/Redis），manifests 以 secretKeyRef 引用。
4. `kustomize build deploy/k8s/overlays/staging | kubectl apply -f -`（或 Config Sync GitOps）。
5. 叢集內跑 `scripts/deploy_smoke.py` + egress/隔離行為驗證 → `@gateB` 綠 → 套 prod overlay。

## 已知佔位（部署前須補）
- Envoy proxy-wasm 的 5 個 `.wasm` 與 filter 設定為佔位（image build 階段落地）。
- `master_authorized_cidrs` 預設空（補維運/Cloud Build CIDR）。
- Cloud SQL `audit_logs` append-only（`REVOKE UPDATE,DELETE`）屬 schema migration，非 IaC。
- platform ns 的 cloudsql-proxy/external-secrets egress NetworkPolicy 待啟用時補。
