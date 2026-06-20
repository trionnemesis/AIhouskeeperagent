# Workload Identity：各 namespace KSA → GSA 綁定，最小權限。
# Why: pod 不持金鑰；Cloud SQL 連線與 Secret 讀取以 IAM 授權，權限按 ns 職責收斂。
#
# 綁定的 KSA 命名約定（k8s 端 ServiceAccount 須一致）：
#   hermes_app  → ns tenant-<id> 的 SA 'hermes' / 'edge' / 'domain-mcp'
#   data_mcp    → ns data-mcp    的 SA 'data-mcp'
#   platform    → ns platform    的 SA 'cloudsql-proxy' / 'external-secrets'
#   gateway     → ns gateway     的 SA 'envoy-egress'

locals {
  # GSA → 允許 impersonate 的 KSA（"<namespace>/<ksa-name>"）。
  wi_bindings = {
    hermes_app = ["tenant-demo/hermes", "tenant-demo/edge", "tenant-demo/domain-mcp"]
    data_mcp   = ["data-mcp/data-mcp", "data-mcp/etl"]
    platform   = ["platform/cloudsql-proxy", "platform/external-secrets"]
    gateway    = ["gateway/envoy-egress"]
  }
}

# ---- GSAs（每工作負載群一個，職責隔離） ----

resource "google_service_account" "hermes_app" {
  account_id   = "${var.cluster_name}-${var.env}-hermes-app"
  display_name = "Hermes tenant workloads (edge/hermes/domain-mcp)"
}

resource "google_service_account" "data_mcp" {
  account_id   = "${var.cluster_name}-${var.env}-data-mcp"
  display_name = "Data MCP workloads (lvr/public-safety/etl)"
}

resource "google_service_account" "platform" {
  account_id   = "${var.cluster_name}-${var.env}-platform"
  display_name = "Platform workloads (cloudsql-proxy/external-secrets)"
}

resource "google_service_account" "gateway" {
  account_id   = "${var.cluster_name}-${var.env}-gateway"
  display_name = "Envoy egress gateway"
}

# ---- Workload Identity 綁定（KSA impersonate GSA） ----

resource "google_service_account_iam_member" "wi_hermes_app" {
  for_each           = toset(local.wi_bindings.hermes_app)
  service_account_id = google_service_account.hermes_app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${each.value}]"
}

resource "google_service_account_iam_member" "wi_data_mcp" {
  for_each           = toset(local.wi_bindings.data_mcp)
  service_account_id = google_service_account.data_mcp.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${each.value}]"
}

resource "google_service_account_iam_member" "wi_platform" {
  for_each           = toset(local.wi_bindings.platform)
  service_account_id = google_service_account.platform.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${each.value}]"
}

resource "google_service_account_iam_member" "wi_gateway" {
  for_each           = toset(local.wi_bindings.gateway)
  service_account_id = google_service_account.gateway.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${each.value}]"
}

# ---- 最小權限 project-level roles ----

# Cloud SQL Client：僅實際連 DB 的工作負載。
resource "google_project_iam_member" "sql_client_hermes_app" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.hermes_app.email}"
}

resource "google_project_iam_member" "sql_client_data_mcp" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.data_mcp.email}"
}

resource "google_project_iam_member" "sql_client_platform" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.platform.email}"
}

# Cloud SQL IAM 登入（IAM DB auth 所需）。
resource "google_project_iam_member" "sql_instance_user_hermes_app" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.hermes_app.email}"
}

resource "google_project_iam_member" "sql_instance_user_data_mcp" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.data_mcp.email}"
}

# Secret Accessor：讀取（非管理）Secret。external-secrets 與實際消費 secret 的工作負載。
resource "google_project_iam_member" "secret_accessor_platform" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.platform.email}"
}

resource "google_project_iam_member" "secret_accessor_hermes_app" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.hermes_app.email}"
}

resource "google_project_iam_member" "secret_accessor_gateway" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.gateway.email}"
}
