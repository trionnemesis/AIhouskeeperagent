# Artifact Registry：docker repo 'hermes'。
# Why: image 來源唯一；tag 由 CI pin（禁 :latest, OPS-1）。對應佔位 REGION-docker.pkg.dev/PROJECT/hermes/<component>:vX。

resource "google_artifact_registry_repository" "hermes" {
  location      = var.region
  repository_id = "hermes"
  description   = "Hermes real-estate component images（tag pinned；禁 :latest, OPS-1）"
  format        = "DOCKER"

  labels = local.common_labels
}
