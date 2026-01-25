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

output "secrets_created" {
  description = "Secrets created in Secret Manager"
  value       = ["openai-api-key", "anthropic-api-key"]
}
