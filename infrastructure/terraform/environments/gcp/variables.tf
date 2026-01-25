# CLARISSA Infrastructure - GCP Variables

# ============================================================
# Project Settings
# ============================================================

variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for Cloud Run"
  type        = string
  default     = "europe-west1"
}

variable "firestore_location" {
  description = "Firestore database location"
  type        = string
  default     = "eur3"  # Europe multi-region
}

# ============================================================
# API Service Configuration
# ============================================================

variable "api_image" {
  description = "Docker image for CLARISSA API"
  type        = string
  default     = "registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/api:latest"
}

variable "api_min_instances" {
  description = "Minimum number of API instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum number of API instances"
  type        = number
  default     = 3
}

variable "api_cpu" {
  description = "CPU limit for API containers"
  type        = string
  default     = "1"
}

variable "api_memory" {
  description = "Memory limit for API containers"
  type        = string
  default     = "1Gi"
}

variable "api_public" {
  description = "Allow unauthenticated access to API"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

# ============================================================
# Secrets (sensitive)
# ============================================================

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude"
  type        = string
  sensitive   = true
}

variable "gitlab_deploy_token" {
  description = "GitLab Deploy Token for registry access"
  type        = string
  sensitive   = true
  default     = ""
}
