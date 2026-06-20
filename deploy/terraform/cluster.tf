# GKE Autopilot 私有叢集。
# Why: Autopilot 強制 runAsNonRoot/no-privileged 等 pod 安全預設；私有節點 + master 授權網路收斂攻擊面。

resource "google_container_cluster" "hermes" {
  name     = "${var.cluster_name}-${var.env}"
  location = var.region # regional = 多 zone HA

  # Autopilot：節點由 Google 託管，無 node_pool 區塊。
  enable_autopilot = true

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.gke.id

  release_channel {
    channel = "REGULAR"
  }

  # Workload Identity：KSA→GSA 映射，pod 不放 GCP 金鑰（iam_wi.tf 綁定）。
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # 私有叢集：私有節點、私有控制面 endpoint。
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # 控制面仍可經授權網路自外部維運觸達；true=純私有
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # 控制面授權網路：kube-API 僅限維運網段 / Cloud Build。
  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.master_authorized_cidrs
      content {
        cidr_block   = cidr_blocks.value.cidr_block
        display_name = cidr_blocks.value.display_name
      }
    }
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # NetworkPolicy（egress default-deny 由 k8s manifest 落地；此處確保 dataplane 支援）。
  # Autopilot 採 Dataplane V2，原生支援 NetworkPolicy，無需額外 addon 區塊。

  # 刪除保護：prod 防誤刪。
  deletion_protection = var.env == "prod"

  resource_labels = local.common_labels

  # private_service_range 必須先建好（Cloud SQL 同網路），避免 peering 競態。
  depends_on = [google_service_networking_connection.private_vpc_connection]
}
