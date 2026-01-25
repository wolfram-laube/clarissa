# CLARISSA Infrastructure - Local K8s Variables

# ============================================================
# Kubernetes Configuration
# ============================================================

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "kubeconfig_context" {
  description = "Kubernetes context to use"
  type        = string
  default     = ""  # Empty = current context
}

variable "namespace" {
  description = "Kubernetes namespace for CLARISSA"
  type        = string
  default     = "clarissa"
}

# ============================================================
# API Configuration
# ============================================================

variable "api_image" {
  description = "Docker image for CLARISSA API"
  type        = string
  default     = "registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/api:latest"
}

variable "api_replicas" {
  description = "Number of API replicas"
  type        = number
  default     = 1
}

variable "api_cpu" {
  description = "CPU limit for API containers"
  type        = string
  default     = "500m"
}

variable "api_memory" {
  description = "Memory limit for API containers"
  type        = string
  default     = "512Mi"
}

# ============================================================
# LLM Configuration
# ============================================================

variable "llm_provider" {
  description = "LLM provider: ollama, anthropic, openai"
  type        = string
  default     = "ollama"
}

variable "ollama_model" {
  description = "Ollama model to use"
  type        = string
  default     = "llama3.2:3b"
}

variable "anthropic_api_key" {
  description = "Anthropic API key (if using Claude)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (if using GPT)"
  type        = string
  sensitive   = true
  default     = ""
}

# ============================================================
# Component Deployment Toggles
# ============================================================

variable "deploy_ollama" {
  description = "Deploy Ollama for local LLM"
  type        = bool
  default     = true
}

variable "deploy_mongodb" {
  description = "Deploy MongoDB via Helm"
  type        = bool
  default     = true
}

variable "deploy_qdrant" {
  description = "Deploy Qdrant vector database"
  type        = bool
  default     = true
}

variable "deploy_ingress" {
  description = "Deploy Ingress resource"
  type        = bool
  default     = false
}

# ============================================================
# Ingress Configuration
# ============================================================

variable "ingress_host" {
  description = "Hostname for Ingress"
  type        = string
  default     = "clarissa.local"
}

# ============================================================
# Logging
# ============================================================

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "DEBUG"
}
