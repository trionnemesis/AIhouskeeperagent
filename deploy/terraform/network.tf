# VPC / subnet / Cloud Router / Cloud NAT。
# Why: 私有叢集無公開節點 IP；唯一對外路徑 = Cloud NAT（集中受控 egress, DI-4 配套）。

resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-${var.env}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "gke" {
  name          = "${var.cluster_name}-${var.env}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = "10.10.0.0/20"

  # 私有 Google 存取：節點無外部 IP 也能達 Google API（Artifact Registry / Cloud SQL admin 等）。
  private_ip_google_access = true

  # Autopilot 叢集所需的 Pod / Service 次要範圍。
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.20.0.0/16"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.30.0.0/20"
  }
}

# Private Services Access：Cloud SQL private IP 需要的對等網段（VPC peering 給 Google 託管網路）。
resource "google_compute_global_address" "private_service_range" {
  name          = "${var.cluster_name}-${var.env}-psa"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]
}

resource "google_compute_router" "router" {
  name    = "${var.cluster_name}-${var.env}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

# Cloud NAT：私有節點唯一受控出向。配合 NetworkPolicy egress default-deny，
# 真正可達 0.0.0.0/0 的只有 Envoy egress gateway pod（DI-4 不可繞過）。
resource "google_compute_router_nat" "nat" {
  name                               = "${var.cluster_name}-${var.env}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
