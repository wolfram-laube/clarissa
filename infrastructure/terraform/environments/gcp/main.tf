# CLARISSA Infrastructure - GCP Environment
#
# Deploys CLARISSA to Google Cloud Platform using:
# - Cloud Run for services
# - Secret Manager for credentials
# - Firestore for database
# - Cloud Monitoring for observability
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state in GCS (uncomment after bucket exists)
  # backend "gcs" {
  #   bucket = "clarissa-terraform-state"
  #   prefix = "gcp/state"
  # }
}

# ============================================================
# Provider Configuration
# ============================================================

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# ============================================================
# Enable Required APIs
# ============================================================

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project = var.gcp_project
  service = each.value

  disable_on_destroy = false
}

# ============================================================
# Secrets
# ============================================================

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  project   = var.gcp_project

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "anthropic_api_key" {
  secret      = google_secret_manager_secret.anthropic_api_key.id
  secret_data = var.anthropic_api_key

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# GitLab Registry credentials (for Cloud Run to pull images)
resource "google_secret_manager_secret" "gitlab_registry" {
  secret_id = "gitlab-registry-credentials"
  project   = var.gcp_project

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# ============================================================
# Service Account for Cloud Run
# ============================================================

resource "google_service_account" "clarissa_api" {
  account_id   = "clarissa-api-sa"
  display_name = "CLARISSA API Service Account"
  project      = var.gcp_project
}

# Grant access to secrets
resource "google_secret_manager_secret_iam_member" "api_anthropic_access" {
  secret_id = google_secret_manager_secret.anthropic_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.clarissa_api.email}"
}

# Grant access to Firestore
resource "google_project_iam_member" "api_firestore_access" {
  project = var.gcp_project
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.clarissa_api.email}"
}

# ============================================================
# Cloud Run: CLARISSA API
# ============================================================

resource "google_cloud_run_v2_service" "clarissa_api" {
  name     = "clarissa-api"
  location = var.gcp_region
  project  = var.gcp_project

  template {
    service_account = google_service_account.clarissa_api.email

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    containers {
      image = var.api_image

      ports {
        container_port = 8000
      }

      env {
        name  = "ENVIRONMENT"
        value = "gcp"
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name  = "LLM_PROVIDER"
        value = "anthropic"
      }

      env {
        name  = "FIRESTORE_PROJECT"
        value = var.gcp_project
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.api_cpu
          memory = var.api_memory
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds = 30
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_version.anthropic_api_key,
  ]
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.api_public ? 1 : 0

  project  = var.gcp_project
  location = var.gcp_region
  name     = google_cloud_run_v2_service.clarissa_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================
# Firestore Database
# ============================================================

resource "google_firestore_database" "clarissa" {
  project     = var.gcp_project
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}
