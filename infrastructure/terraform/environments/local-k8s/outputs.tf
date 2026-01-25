# CLARISSA Infrastructure - Local K8s Outputs

output "namespace" {
  description = "Kubernetes namespace"
  value       = kubernetes_namespace.clarissa.metadata[0].name
}

output "api_service" {
  description = "API Service name"
  value       = kubernetes_service.clarissa_api.metadata[0].name
}

output "port_forward_command" {
  description = "Command to access API locally"
  value       = "kubectl port-forward -n ${kubernetes_namespace.clarissa.metadata[0].name} svc/clarissa-api 8000:80"
}

output "api_url" {
  description = "API URL (after port-forward)"
  value       = "http://localhost:8000"
}

output "ollama_deployed" {
  description = "Whether Ollama was deployed"
  value       = var.deploy_ollama
}

output "mongodb_deployed" {
  description = "Whether MongoDB was deployed"
  value       = var.deploy_mongodb
}
