# CLARISSA Infrastructure - GCP Environment
#
# Deploys CLARISSA to Google Cloud Platform using:
# - Cloud Run for services
# - Secret Manager for credentials
# - Firestore for database
# - Cloud Monitoring for observability
#
# Multi-Provider LLM Support:
# - OpenAI (primary - cost effective)
# - Anthropic (fallback - quality)
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
# Artifact Registry - Remote Repository for GitLab
# ============================================================

# Remote repository that proxies GitLab Container Registry
# This allows Cloud Run to pull images from GitLab via AR
resource "google_artifact_registry_repository" "gitlab_remote" {
  location      = var.gcp_region
  repository_id = "gitlab-remote"
  description   = "Remote repository proxying GitLab Container Registry"
  format        = "DOCKER"
  mode          = "REMOTE_REPOSITORY"

  remote_repository_config {
    description = "GitLab Container Registry"
    docker_repository {
      custom_repository {
        uri = "https://registry.gitlab.com"
      }
    }
    upstream_credentials {
      username_password_credentials {
        username                = var.gitlab_deploy_username
        password_secret_version = google_secret_manager_secret_version.gitlab_registry.name
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}




# ============================================================
# Secrets - LLM API Keys
# ============================================================

# OpenAI API Key (primary provider - cost effective)
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  project   = var.gcp_project

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# Anthropic API Key (fallback provider)
# Always create the secret, but version only if key provided
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
  # Use placeholder if not provided - app will handle empty gracefully
  secret_data = var.anthropic_api_key != "" ? var.anthropic_api_key : "not-configured"

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

# GitLab Deploy Token for AR Remote Repository
resource "google_secret_manager_secret_version" "gitlab_registry" {
  secret      = google_secret_manager_secret.gitlab_registry.id
  secret_data = var.gitlab_deploy_token

  lifecycle {
    ignore_changes = [secret_data]
  }
}


# ============================================================
# Service Account for Cloud Run
# ============================================================

resource "google_service_account" "clarissa_api" {
  account_id   = "clarissa-api-sa"
  display_name = "CLARISSA API Service Account"
  project      = var.gcp_project
}

# Grant access to OpenAI secret
resource "google_secret_manager_secret_iam_member" "api_openai_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.clarissa_api.email}"
}

# Grant access to Anthropic secret
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

      # Environment Configuration
      env {
        name  = "ENVIRONMENT"
        value = "gcp"
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name  = "DEBUG"
        value = "false"
      }

      # LLM Provider Configuration
      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }

      env {
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }

      env {
        name  = "ANTHROPIC_MODEL"
        value = var.anthropic_model
      }

      # Database Configuration
      env {
        name  = "FIRESTORE_PROJECT"
        value = var.gcp_project
      }

      # Disable emulator in GCP
      env {
        name  = "FIRESTORE_EMULATOR_HOST"
        value = ""
      }

      # OpenAI API Key (from Secret Manager)
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      # Anthropic API Key (from Secret Manager)
      # Will be "not-configured" if not provided - app handles this
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
    google_secret_manager_secret_version.openai_api_key,
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
