# CLARISSA Infrastructure - GCP Outputs

output "api_url" {
  description = "CLARISSA API URL"
  value       = google_cloud_run_v2_service.clarissa_api.uri
}

output "api_service_account" {
  description = "API Service Account email"
  value       = google_service_account.clarissa_api.email
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.clarissa.name
}

output "project" {
  description = "GCP Project ID"
  value       = var.gcp_project
}

output "region" {
  description = "GCP Region"
  value       = var.gcp_region
}

# LLM Configuration
output "llm_provider" {
  description = "Primary LLM provider"
  value       = var.llm_provider
}

output "llm_fallback_enabled" {
  description = "Whether Anthropic fallback is enabled"
  value       = var.anthropic_api_key != ""
}

output "secrets_configured" {
  description = "List of configured secrets"
  value = compact([
    "openai-api-key",
    var.anthropic_api_key != "" ? "anthropic-api-key" : "",
  ])
}
