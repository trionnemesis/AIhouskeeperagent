# Cloud SQL for PostgreSQL：一實例多 DB（per-tenant + 共用 data_mcp）。
# Why: regional HA + PITR 滿足可用性/稽核；private IP 不對外，僅經 Auth Proxy + Workload Identity 連線。

resource "google_sql_database_instance" "pg" {
  name             = "${var.cluster_name}-${var.env}-pg"
  database_version = "POSTGRES_15"
  region           = var.region

  # prod 防誤刪；staging 允許 terraform destroy。
  deletion_protection = var.env == "prod"

  settings {
    tier              = var.cloudsql_tier
    availability_type = "REGIONAL" # regional HA（自動 failover）
    disk_type         = "PD_SSD"
    disk_size         = 20
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true # PITR（WAL 歸檔）
      start_time                     = "18:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 14
      }
    }

    ip_configuration {
      ipv4_enabled    = false # 無公開 IP
      private_network = google_compute_network.vpc.id
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    # IAM 資料庫驗證：搭配 Workload Identity，pod 不放 DB 密碼。
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    user_labels = local.common_labels
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Per-tenant database：tenant_<id>（dash 轉 underscore 以符合 Postgres 識別字）。
resource "google_sql_database" "tenant" {
  for_each = toset(var.tenant_ids)
  name     = "tenant_${replace(each.value, "-", "_")}"
  instance = google_sql_database_instance.pg.name
}

# 共用 data_mcp database（公開參考資料，非 tenant-scoped）。
resource "google_sql_database" "data_mcp" {
  name     = "data_mcp"
  instance = google_sql_database_instance.pg.name
}

# 應用程式 IAM 使用者（GSA 對應）。Cloud SQL IAM user 名 = service account email 去掉 .gserviceaccount.com 後綴。
resource "google_sql_user" "hermes_app" {
  name     = trimsuffix(google_service_account.hermes_app.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.pg.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

resource "google_sql_user" "data_mcp" {
  name     = trimsuffix(google_service_account.data_mcp.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.pg.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
