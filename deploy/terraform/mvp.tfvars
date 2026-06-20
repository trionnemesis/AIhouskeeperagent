# MVP 最小規格（省錢）— 以 -var-file=mvp.tfvars 套用。
# 砍掉最大宗成本：Cloud SQL 改單區非 HA + 最小機型 + 關 PITR；Redis 改 BASIC 單節點。
# prod 請勿用此檔（無 HA）。對應 spec-kit/06-platform-gke（MVP 先單租戶）。

env        = "staging"
tenant_ids = ["tenant-demo"]

# Cloud SQL：最大省錢項
cloudsql_tier              = "db-f1-micro" # 共享核心，最小（cache/MVP 足夠）
cloudsql_availability_type = "ZONAL"       # 非 HA
cloudsql_disk_size         = 10            # 最小
cloudsql_pitr              = false         # 關 WAL 歸檔

# Memorystore：BASIC 單節點 1GB
redis_tier = "BASIC"
