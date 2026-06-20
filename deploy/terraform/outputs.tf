# Outputs：供 kubeconfig / Auth Proxy / CI image push 取用。

output "cluster_name" {
  description = "GKE 叢集名稱。"
  value       = google_container_cluster.hermes.name
}

output "cluster_endpoint" {
  description = "GKE 控制面 endpoint（私有；經授權網路觸達）。"
  value       = google_container_cluster.hermes.endpoint
  sensitive   = true
}

output "cluster_location" {
  description = "叢集 region。"
  value       = google_container_cluster.hermes.location
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name（Auth Proxy 用：project:region:instance）。"
  value       = google_sql_database_instance.pg.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL private IP。"
  value       = google_sql_database_instance.pg.private_ip_address
  sensitive   = true
}

output "redis_host" {
  description = "Memorystore Redis host（私有）。"
  value       = google_redis_instance.redis.host
  sensitive   = true
}

output "artifact_registry_url" {
  description = "Docker registry base URL（image 前綴）。"
  value       = "${google_artifact_registry_repository.hermes.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.hermes.repository_id}"
}

output "workload_identity_service_accounts" {
  description = "各工作負載群 GSA email（k8s SA annotation 用）。"
  value = {
    hermes_app = google_service_account.hermes_app.email
    data_mcp   = google_service_account.data_mcp.email
    platform   = google_service_account.platform.email
    gateway    = google_service_account.gateway.email
  }
}
