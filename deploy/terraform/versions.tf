# Terraform 與 provider 版本約束。
# Why: pin provider major 以避免 GKE/Cloud SQL resource schema 漂移破壞 plan。

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0, < 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0, < 6.0"
    }
  }

  # Remote state 後端（GCS）。佔位：實際 bucket 由平台預先建立（chicken-egg，不由本 stack 管）。
  # 啟用前先 `gsutil mb -l <region> gs://<state-bucket>` 並開啟 versioning。
  # backend "gcs" {
  #   bucket = "hermes-tfstate-PLACEHOLDER"
  #   prefix = "hermes-real-estate/infra"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
