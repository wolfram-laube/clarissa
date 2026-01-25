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
  default     = "registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:latest"
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
# LLM Provider Configuration
# ============================================================

variable "llm_provider" {
  description = "Primary LLM provider (openai, anthropic, ollama)"
  type        = string
  default     = "openai"  # OpenAI is more cost-effective

  validation {
    condition     = contains(["openai", "anthropic", "ollama"], var.llm_provider)
    error_message = "llm_provider must be one of: openai, anthropic, ollama"
  }
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
# Secrets (sensitive)
# ============================================================

variable "openai_api_key" {
  description = "OpenAI API key (primary provider)"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key (fallback provider, optional)"
  type        = string
  sensitive   = true
  default     = ""  # Optional - only needed for fallback
}

variable "gitlab_deploy_token" {
  description = "GitLab Deploy Token for registry access"
  type        = string
  sensitive   = true
  default     = ""
}
