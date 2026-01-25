# CLARISSA Infrastructure - Local Kubernetes Environment
#
# Deploys CLARISSA to local K8s (K3s, minikube, kind) using:
# - Kubernetes Deployments for services
# - Kubernetes Secrets for credentials
# - MongoDB for database (or PostgreSQL)
#
# Prerequisites:
#   - K3s: k3d cluster create clarissa
#   - minikube: minikube start
#   - kind: kind create cluster
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  # Local state (no remote backend needed for local dev)
  backend "local" {
    path = "terraform.tfstate"
  }
}

# ============================================================
# Provider Configuration
# ============================================================

provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kubeconfig_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kubeconfig_context
  }
}

# ============================================================
# Namespace
# ============================================================

resource "kubernetes_namespace" "clarissa" {
  metadata {
    name = var.namespace

    labels = {
      app        = "clarissa"
      managed-by = "terraform"
    }
  }
}

# ============================================================
# Secrets
# ============================================================

resource "kubernetes_secret" "clarissa_secrets" {
  metadata {
    name      = "clarissa-secrets"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  data = {
    ANTHROPIC_API_KEY = var.anthropic_api_key
    OPENAI_API_KEY    = var.openai_api_key
  }

  type = "Opaque"
}

# ============================================================
# ConfigMap
# ============================================================

resource "kubernetes_config_map" "clarissa_config" {
  metadata {
    name      = "clarissa-config"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  data = {
    ENVIRONMENT    = "local-k8s"
    LOG_LEVEL      = var.log_level
    LLM_PROVIDER   = var.llm_provider
    OLLAMA_HOST    = "http://ollama:11434"
    OLLAMA_MODEL   = var.ollama_model
    MONGODB_URI    = "mongodb://mongodb:27017/clarissa"
    QDRANT_HOST    = "http://qdrant:6333"
  }
}

# ============================================================
# CLARISSA API Deployment
# ============================================================

resource "kubernetes_deployment" "clarissa_api" {
  metadata {
    name      = "clarissa-api"
    namespace = kubernetes_namespace.clarissa.metadata[0].name

    labels = {
      app       = "clarissa"
      component = "api"
    }
  }

  spec {
    replicas = var.api_replicas

    selector {
      match_labels = {
        app       = "clarissa"
        component = "api"
      }
    }

    template {
      metadata {
        labels = {
          app       = "clarissa"
          component = "api"
        }
      }

      spec {
        container {
          name  = "api"
          image = var.api_image

          port {
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.clarissa_config.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.clarissa_secrets.metadata[0].name
            }
          }

          resources {
            limits = {
              cpu    = var.api_cpu
              memory = var.api_memory
            }
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 30
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "clarissa_api" {
  metadata {
    name      = "clarissa-api"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    selector = {
      app       = "clarissa"
      component = "api"
    }

    port {
      port        = 80
      target_port = 8000
    }

    type = "ClusterIP"
  }
}

# ============================================================
# Ollama (Local LLM)
# ============================================================

resource "kubernetes_deployment" "ollama" {
  count = var.deploy_ollama ? 1 : 0

  metadata {
    name      = "ollama"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ollama"
      }
    }

    template {
      metadata {
        labels = {
          app = "ollama"
        }
      }

      spec {
        container {
          name  = "ollama"
          image = "ollama/ollama:latest"

          port {
            container_port = 11434
          }

          resources {
            limits = {
              cpu    = "2"
              memory = "4Gi"
            }
          }

          volume_mount {
            name       = "ollama-data"
            mount_path = "/root/.ollama"
          }
        }

        volume {
          name = "ollama-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.ollama[0].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "ollama" {
  count = var.deploy_ollama ? 1 : 0

  metadata {
    name      = "ollama-data"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_service" "ollama" {
  count = var.deploy_ollama ? 1 : 0

  metadata {
    name      = "ollama"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    selector = {
      app = "ollama"
    }

    port {
      port        = 11434
      target_port = 11434
    }
  }
}

# ============================================================
# MongoDB (via Helm)
# ============================================================

resource "helm_release" "mongodb" {
  count = var.deploy_mongodb ? 1 : 0

  name       = "mongodb"
  namespace  = kubernetes_namespace.clarissa.metadata[0].name
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "mongodb"
  version    = "14.8.3"

  set {
    name  = "auth.enabled"
    value = "false"
  }

  set {
    name  = "persistence.size"
    value = "5Gi"
  }
}

# ============================================================
# Qdrant (Vector DB)
# ============================================================

resource "kubernetes_deployment" "qdrant" {
  count = var.deploy_qdrant ? 1 : 0

  metadata {
    name      = "qdrant"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "qdrant"
      }
    }

    template {
      metadata {
        labels = {
          app = "qdrant"
        }
      }

      spec {
        container {
          name  = "qdrant"
          image = "qdrant/qdrant:latest"

          port {
            container_port = 6333
          }

          volume_mount {
            name       = "qdrant-data"
            mount_path = "/qdrant/storage"
          }
        }

        volume {
          name = "qdrant-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.qdrant[0].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "qdrant" {
  count = var.deploy_qdrant ? 1 : 0

  metadata {
    name      = "qdrant-data"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
  }
}

resource "kubernetes_service" "qdrant" {
  count = var.deploy_qdrant ? 1 : 0

  metadata {
    name      = "qdrant"
    namespace = kubernetes_namespace.clarissa.metadata[0].name
  }

  spec {
    selector = {
      app = "qdrant"
    }

    port {
      port        = 6333
      target_port = 6333
    }
  }
}

# ============================================================
# Ingress (optional)
# ============================================================

resource "kubernetes_ingress_v1" "clarissa" {
  count = var.deploy_ingress ? 1 : 0

  metadata {
    name      = "clarissa-ingress"
    namespace = kubernetes_namespace.clarissa.metadata[0].name

    annotations = {
      "kubernetes.io/ingress.class" = "traefik"
    }
  }

  spec {
    rule {
      host = var.ingress_host

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.clarissa_api.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}
