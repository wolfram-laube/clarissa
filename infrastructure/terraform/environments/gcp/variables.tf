# CLARISSA Infrastructure - GCP Variables
# Validated: 2026-01-25 via GitLab CI/CD Pipeline

# ============================================================
# Project Settings
# ============================================================

variable "gcp_project" {
  description = "GCP Project ID for CLARISSA deployment"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources"
  type        = string
  default     = "europe-west1"
}

# ============================================================
# LLM Provider Configuration
# ============================================================

variable "llm_provider" {
  description = "Primary LLM provider (openai, anthropic, ollama)"
  type        = string
  default     = "openai"

  validation {
    condition     = contains(["openai", "anthropic", "ollama"], var.llm_provider)
    error_message = "llm_provider must be one of: openai, anthropic, ollama"
  }
}

variable "openai_api_key" {
  description = "OpenAI API Key (primary provider)"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API Key (fallback provider)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_model" {
  description = "OpenAI model to use"
  type        = string
  default     = "gpt-4o"
}

variable "anthropic_model" {
  description = "Anthropic model to use"
  type        = string
  default     = "claude-sonnet-4-20250514"
}

# ============================================================
# Cloud Run Configuration
# ============================================================

variable "api_image" {
  description = "Docker image for CLARISSA API"
  type        = string
  default     = "europe-west1-docker.pkg.dev/myk8sproject-207017/gitlab-remote/wolfram_laube/blauweiss_llc/clarissa/api:latest"
}

variable "api_min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

variable "api_cpu" {
  description = "CPU allocation for API containers"
  type        = string
  default     = "1"
}

variable "api_memory" {
  description = "Memory allocation for API containers"
  type        = string
  default     = "512Mi"
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
# Firestore Configuration
# ============================================================

variable "firestore_location" {
  description = "Firestore database location"
  type        = string
  default     = "eur3"
}