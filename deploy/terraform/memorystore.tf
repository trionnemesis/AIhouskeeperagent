# Memorystore for Redis：dedup / reply token / 並發閘狀態（Inv-9, REL-1/2）。
# Why: STANDARD_HA 跨 zone 複本，避免單點導致重送/並發閘失效。

resource "google_redis_instance" "redis" {
  name           = "${var.cluster_name}-${var.env}-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 1
  region         = var.region

  # 私有 VPC 連線（直連 VPC，非對外）。
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version           = "REDIS_7_0"
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  auth_enabled            = true

  labels = local.common_labels

  depends_on = [google_service_networking_connection.private_vpc_connection]
}
