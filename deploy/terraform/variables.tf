# 輸入變數：project/region 全變數化，無 secret 值。

variable "project_id" {
  description = "GCP project id（部署目標）。"
  type        = string
}

variable "region" {
  description = "主要 region。資料落地境內考量，預設台灣 asia-east1。"
  type        = string
  default     = "asia-east1"
}

variable "zone" {
  description = "預設 zone（provider 層級；regional 資源不依賴）。"
  type        = string
  default     = "asia-east1-a"
}

variable "env" {
  description = "環境名（staging/prod），用於資源命名與標籤。"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "prod"], var.env)
    error_message = "env 僅允許 staging 或 prod。"
  }
}

variable "tenant_ids" {
  description = "租戶清單。namespace-per-tenant 隔離；每租戶一份 Cloud SQL database 'tenant_<id>'。MVP 單租戶 tenant-demo。"
  type        = list(string)
  default     = ["tenant-demo"]
}

variable "master_authorized_cidrs" {
  description = "kube-API 控制面授權網路（維運網段/Cloud Build）。預設空 = 僅私有路徑可達；佈署前須補維運 CIDR。"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

variable "cluster_name" {
  description = "GKE 叢集名稱前綴。"
  type        = string
  default     = "hermes"
}

variable "cloudsql_tier" {
  description = "Cloud SQL 機型。prod 建議 Enterprise Plus 或更高，staging 可降規。"
  type        = string
  default     = "db-custom-2-7680"
}

# 成本旋鈕（prod 預設高可用；MVP 以 mvp.tfvars 降規省錢）。
variable "cloudsql_availability_type" {
  description = "Cloud SQL 可用性：REGIONAL(HA, prod) / ZONAL(單區, MVP 省錢)。"
  type        = string
  default     = "REGIONAL"
  validation {
    condition     = contains(["REGIONAL", "ZONAL"], var.cloudsql_availability_type)
    error_message = "僅允許 REGIONAL 或 ZONAL。"
  }
}

variable "cloudsql_disk_size" {
  description = "Cloud SQL 磁碟 GB（最小 10）。"
  type        = number
  default     = 20
}

variable "cloudsql_pitr" {
  description = "Cloud SQL Point-In-Time Recovery（WAL 歸檔；MVP 可關省儲存）。"
  type        = bool
  default     = true
}

variable "redis_tier" {
  description = "Memorystore 層級：STANDARD_HA(跨區複本, prod) / BASIC(單節點, MVP 省錢)。"
  type        = string
  default     = "STANDARD_HA"
  validation {
    condition     = contains(["STANDARD_HA", "BASIC"], var.redis_tier)
    error_message = "僅允許 STANDARD_HA 或 BASIC。"
  }
}

# 共用標籤（GCP resource labels；值須符合 GCP 規則：小寫/數字/dash/underscore）。
locals {
  common_labels = {
    "app_kubernetes_io_part-of" = "hermes-real-estate"
    "managed-by"                = "terraform"
    "env"                       = var.env
  }
}
