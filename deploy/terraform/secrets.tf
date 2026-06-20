# Secret Manager：僅建立 secret 容器，值不入版控。
# Why: 名稱與用途集中管理（configuration.md）；版本值經密管/CI 注入，Terraform 不持明文。
#
# 注入方式：佈署或 CI pipeline 以
#   gcloud secrets versions add <name> --data-file=- < <source>
# 寫入版本；k8s 端以 External Secrets / CSI driver 經 platform GSA（Secret Accessor）讀取。

locals {
  # secret 名稱清單（值不在此）。LINE 通道 + 資料層 + 模型路由（configuration.md）。
  secret_names = [
    "LINE_CHANNEL_SECRET",       # HMAC-SHA256 驗章（SEC-4）
    "LINE_CHANNEL_ACCESS_TOKEN", # reply/push 出口
    "LINE_HOME_CHANNEL",         # Cron 主動推播目標（C9）
    "DATABASE_URL",              # Postgres 連線字串（prod）
    "REDIS_URL",                 # Redis 連線字串（含 auth）
    "OPENROUTER_API_KEY",        # 模型路由統一入口（COST-2）
    "GROQ_API_KEY",              # STT whisper（C3）
  ]
}

resource "google_secret_manager_secret" "app" {
  for_each  = toset(local.secret_names)
  secret_id = each.value

  replication {
    user_managed {
      replicas {
        location = var.region # 資料落地境內：限定 region 複本
      }
    }
  }

  labels = local.common_labels

  # 註：不建立 google_secret_manager_secret_version —— 值經密管注入，杜絕明文入版控。
}
