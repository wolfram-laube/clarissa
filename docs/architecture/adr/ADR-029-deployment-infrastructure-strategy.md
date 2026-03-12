> ⚠️ **DEPRECATED** — Diese ADR wurde als company-level BW-ADR-010 in [ops/adr](https://gitlab.com/wolfram_laube/blauweiss_llc/ops/adr) migriert (2026-03-12). Bitte BW-ADR-010 als maßgebliche Referenz verwenden.
>
> Die CLARISSA-spezifischen Implementierungsdetails in diesem Dokument bleiben als historische Referenz erhalten.

---

# ADR-029: Deployment & Infrastructure Strategy

| Status | Proposed |
|--------|----------|
| Date | 2026-01-24 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-024 (Core System), ADR-025 (LLM Integration), ADR-026 (Testing) |

---

## Context

CLARISSA braucht eine solide Infrastruktur-Basis bevor wir mit der eigentlichen Implementierung beginnen. Die Fragen:

1. **Infrastructure as Code**: Wie definieren wir die Cloud-Ressourcen?
2. **Deployment**: Wie kommen Services in die Cloud?
3. **Secrets**: Wie verwalten wir API-Keys, Credentials?
4. **Environments**: Dev, Staging, Prod - was brauchen wir wann?
5. **GitOps**: Brauchen wir ArgoCD/Flux oder reicht GitLab CI?

### Constraints

- **Kleines Team**: 4 Personen (Wolfram + 3 Consultants)
- **Budget**: Startup-Phase, Kosten minimieren
- **Flexibilität**: Muss später für Air-Gapped Deployments adaptierbar sein
- **Bestehende Infra**: GitLab CI mit 12 Runnern bereits vorhanden
- **GCP Projekt**: `myk8sproject-207017` existiert bereits

---

## Decision

### Prinzip: "Pragmatisch, aber reproduzierbar"

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   "So einfach wie möglich, aber nicht einfacher."                               │
│                                                                                  │
│   ✅ Terraform         → Infrastruktur muss reproduzierbar sein                 │
│   ✅ GitLab CI/CD      → Haben wir schon, funktioniert, reicht                  │
│   ✅ GCP Secret Manager → Native, kein Ops-Overhead                             │
│   ✅ Cloud Run         → Serverless, skaliert, günstig für Start               │
│                                                                                  │
│   ❌ ArgoCD            → Overkill für kleines Team (später optional)            │
│   ❌ Helm              → Cloud Run braucht kein Helm                            │
│   ❌ Vault             → GCP Secret Manager reicht erstmal                      │
│   ❌ Multi-Cluster K8s → Viel zu früh                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DEPLOYMENT FLOW                                     │
│                                                                                  │
│   Developer                                                                      │
│       │                                                                          │
│       │ git push                                                                 │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         GitLab CI/CD                                     │   │
│   │                                                                          │   │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐    │   │
│   │   │   Lint   │──▶│   Test   │──▶│  Build   │──▶│     Deploy       │    │   │
│   │   └──────────┘   └──────────┘   └──────────┘   └──────────────────┘    │   │
│   │                                       │                 │               │   │
│   │                                       ▼                 ▼               │   │
│   │                              ┌──────────────┐   ┌──────────────┐       │   │
│   │                              │   GitLab     │   │   Terraform  │       │   │
│   │                              │   Registry   │   │    Apply     │       │   │
│   │                              └──────────────┘   └──────────────┘       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                 │                        │
│                                       ▼                 ▼                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         Google Cloud Platform                            │   │
│   │                         Project: myk8sproject-207017                     │   │
│   │                                                                          │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│   │   │  Cloud Run  │  │  Firestore  │  │   Secret    │  │   Cloud     │   │   │
│   │   │  Services   │  │  Database   │  │   Manager   │  │  Storage    │   │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│   │                                                                          │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │   │
│   │   │   Cloud     │  │  Artifact   │  │    IAM      │                    │   │
│   │   │  Monitoring │  │  Registry   │  │  Bindings   │                    │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
infrastructure/
├── terraform/
│   │
│   ├── modules/                        # Reusable modules
│   │   ├── cloud-run/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── firestore/
│   │   │   └── ...
│   │   │
│   │   ├── secrets/
│   │   │   └── ...
│   │   │
│   │   ├── iam/
│   │   │   └── ...
│   │   │
│   │   └── monitoring/
│   │       └── ...
│   │
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf                 # Uses modules
│   │   │   ├── variables.tf
│   │   │   ├── terraform.tfvars        # Dev-specific values
│   │   │   └── backend.tf              # GCS state backend
│   │   │
│   │   └── prod/                       # Later
│   │       └── ...
│   │
│   └── README.md
│
├── docker/
│   ├── api/
│   │   └── Dockerfile
│   ├── worker/
│   │   └── Dockerfile
│   └── opm-flow/
│       └── Dockerfile
│
└── scripts/
    ├── setup-gcp.sh                    # Initial GCP setup
    └── deploy.sh                       # Manual deploy helper
```

---

## Terraform Modules

### Cloud Run Module

```hcl
# infrastructure/terraform/modules/cloud-run/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type = string
}

variable "service_name" {
  type = string
}

variable "image" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "secrets" {
  type = list(object({
    env_name    = string
    secret_id   = string
    version     = string
  }))
  default = []
}

variable "min_instances" {
  type    = number
  default = 0  # Scale to zero for dev
}

variable "max_instances" {
  type    = number
  default = 10
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "allow_unauthenticated" {
  type    = bool
  default = false
}

# Service Account for the Cloud Run service
resource "google_service_account" "service" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  project      = var.project_id
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    service_account = google_service_account.service.email

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Static environment variables
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secrets from Secret Manager
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.value.env_name
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = env.value.version
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM: Allow unauthenticated access if specified
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant service account access to secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = { for s in var.secrets : s.secret_id => s }
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.service.email}"
}

output "url" {
  value = google_cloud_run_v2_service.service.uri
}

output "service_account_email" {
  value = google_service_account.service.email
}
```

### Secrets Module

```hcl
# infrastructure/terraform/modules/secrets/main.tf

variable "project_id" {
  type = string
}

variable "secrets" {
  type = map(object({
    description = string
    value       = string  # Will be marked sensitive
  }))
  sensitive = true
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = var.secrets
  project   = var.project_id
  secret_id = each.key

  replication {
    auto {}
  }

  labels = {
    managed_by = "terraform"
  }
}

resource "google_secret_manager_secret_version" "versions" {
  for_each    = var.secrets
  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value.value
}

output "secret_ids" {
  value = { for k, v in google_secret_manager_secret.secrets : k => v.secret_id }
}
```

### Firestore Module

```hcl
# infrastructure/terraform/modules/firestore/main.tf

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "database_id" {
  type    = string
  default = "(default)"
}

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.database_id
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  # Prevents accidental deletion
  deletion_policy = "DELETE"  # Change to "ABANDON" for prod
}

output "database_name" {
  value = google_firestore_database.database.name
}
```

---

## Environment: Dev

```hcl
# infrastructure/terraform/environments/dev/main.tf

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type    = string
  default = "myk8sproject-207017"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

# Firestore Database
module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  region     = var.region
}

# Secrets
module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  
  secrets = {
    "anthropic-api-key" = {
      description = "Anthropic API Key for LLM calls"
      value       = var.anthropic_api_key
    }
    "openai-api-key" = {
      description = "OpenAI API Key (fallback)"
      value       = var.openai_api_key
    }
  }
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

# CLARISSA API Service
module "clarissa_api" {
  source       = "../../modules/cloud-run"
  project_id   = var.project_id
  service_name = "clarissa-api-dev"
  region       = var.region
  
  image = "registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:latest"
  
  min_instances = 0  # Scale to zero
  max_instances = 2
  cpu           = "1"
  memory        = "1Gi"
  
  env_vars = {
    ENVIRONMENT     = "dev"
    LOG_LEVEL       = "DEBUG"
    FIRESTORE_DB    = module.firestore.database_name
  }
  
  secrets = [
    {
      env_name  = "ANTHROPIC_API_KEY"
      secret_id = "anthropic-api-key"
      version   = "latest"
    }
  ]
  
  allow_unauthenticated = true  # For dev/testing
}

# CLARISSA Worker Service (for simulation jobs)
module "clarissa_worker" {
  source       = "../../modules/cloud-run"
  project_id   = var.project_id
  service_name = "clarissa-worker-dev"
  region       = var.region
  
  image = "registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:latest"
  
  min_instances = 0
  max_instances = 5
  cpu           = "2"
  memory        = "4Gi"  # OPM Flow needs more memory
  
  env_vars = {
    ENVIRONMENT  = "dev"
    LOG_LEVEL    = "DEBUG"
    API_URL      = module.clarissa_api.url
  }
  
  allow_unauthenticated = false  # Internal only
}

# Outputs
output "api_url" {
  value = module.clarissa_api.url
}

output "worker_url" {
  value = module.clarissa_worker.url
}
```

### Backend Configuration

```hcl
# infrastructure/terraform/environments/dev/backend.tf

terraform {
  backend "gcs" {
    bucket = "clarissa-terraform-state"
    prefix = "dev"
  }
}
```

---

## GitLab CI Pipeline

```yaml
# .gitlab-ci.yml (infrastructure section)

stages:
  - validate
  - plan
  - apply
  - build
  - deploy

variables:
  TF_ROOT: "infrastructure/terraform/environments/dev"
  TF_STATE_BUCKET: "clarissa-terraform-state"

# ============== TERRAFORM ==============

.terraform:
  image: hashicorp/terraform:1.7
  before_script:
    - cd ${TF_ROOT}
    - terraform init
  tags:
    - docker-any

terraform:validate:
  extends: .terraform
  stage: validate
  script:
    - terraform validate
    - terraform fmt -check
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - infrastructure/terraform/**/*

terraform:plan:
  extends: .terraform
  stage: plan
  script:
    - terraform plan -out=plan.tfplan
  artifacts:
    paths:
      - ${TF_ROOT}/plan.tfplan
    expire_in: 1 day
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - infrastructure/terraform/**/*
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - infrastructure/terraform/**/*

terraform:apply:
  extends: .terraform
  stage: apply
  script:
    - terraform apply -auto-approve plan.tfplan
  dependencies:
    - terraform:plan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - infrastructure/terraform/**/*
      when: manual  # Require manual approval
  environment:
    name: dev
    url: https://clarissa-api-dev-xxxxx.run.app

# ============== DOCKER BUILD ==============

.docker:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  tags:
    - docker-any

build:api:
  extends: .docker
  stage: build
  script:
    - docker build -t registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:${CI_COMMIT_SHA} -f docker/api/Dockerfile .
    - docker push registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:${CI_COMMIT_SHA}
    - docker tag registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:${CI_COMMIT_SHA} registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:latest
    - docker push registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - src/api/**/*
        - docker/api/**/*

build:worker:
  extends: .docker
  stage: build
  script:
    - docker build -t registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:${CI_COMMIT_SHA} -f docker/worker/Dockerfile .
    - docker push registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:${CI_COMMIT_SHA}
    - docker tag registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:${CI_COMMIT_SHA} registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:latest
    - docker push registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - src/worker/**/*
        - docker/worker/**/*

# ============== DEPLOY ==============

deploy:dev:
  image: google/cloud-sdk:slim
  stage: deploy
  script:
    - echo ${GCP_SERVICE_KEY} | gcloud auth activate-service-account --key-file=-
    - gcloud run services update clarissa-api-dev --image registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/api:${CI_COMMIT_SHA} --region europe-west1 --project ${GCP_PROJECT}
    - gcloud run services update clarissa-worker-dev --image registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/worker:${CI_COMMIT_SHA} --region europe-west1 --project ${GCP_PROJECT}
  needs:
    - build:api
    - build:worker
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  environment:
    name: dev
    url: https://clarissa-api-dev-xxxxx.run.app
  tags:
    - docker-any
```

---

## Secrets Management

### Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SECRETS FLOW                                           │
│                                                                                  │
│   ┌─────────────────┐                                                           │
│   │  Developer      │                                                           │
│   │  (one-time)     │                                                           │
│   └────────┬────────┘                                                           │
│            │                                                                     │
│            │  1. Create secrets via Terraform                                   │
│            │     (values from CI variables or manual)                           │
│            ▼                                                                     │
│   ┌─────────────────┐                                                           │
│   │  GCP Secret     │                                                           │
│   │  Manager        │                                                           │
│   └────────┬────────┘                                                           │
│            │                                                                     │
│            │  2. Cloud Run mounts secrets as env vars                           │
│            ▼                                                                     │
│   ┌─────────────────┐                                                           │
│   │  Cloud Run      │  ANTHROPIC_API_KEY=sk-...                                │
│   │  Service        │  (injected at runtime)                                    │
│   └─────────────────┘                                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Required Secrets

| Secret | Description | Used By |
|--------|-------------|---------|
| `anthropic-api-key` | Anthropic Claude API | API Service |
| `openai-api-key` | OpenAI (fallback) | API Service |
| `gitlab-token` | GitLab API access | Worker |
| `google-service-key` | GCP Service Account | CI/CD |

### GitLab CI Variables

```
GCP_PROJECT         = myk8sproject-207017
GCP_SERVICE_KEY     = (JSON key, masked)
ANTHROPIC_API_KEY   = (for Terraform, masked)
OPENAI_API_KEY      = (for Terraform, masked)
TF_VAR_anthropic_api_key = ${ANTHROPIC_API_KEY}
TF_VAR_openai_api_key    = ${OPENAI_API_KEY}
```

---

## Environments

### Phase 1: Dev Only

```
┌─────────────────────────────────────────────────────┐
│                     DEV                              │
│                                                      │
│   clarissa-api-dev      → Scale to zero             │
│   clarissa-worker-dev   → Scale to zero             │
│   Firestore (default)   → Dev data                  │
│                                                      │
│   Cost: ~$0 when idle (scale to zero)               │
└─────────────────────────────────────────────────────┘
```

### Phase 2: Add Staging (wenn nötig)

```
┌─────────────────────────┐  ┌─────────────────────────┐
│          DEV            │  │        STAGING          │
│                         │  │                         │
│   For development       │  │   Pre-production        │
│   Scale to zero         │  │   Mirrors prod config   │
│   Debug logging         │  │   Limited scale         │
└─────────────────────────┘  └─────────────────────────┘
```

### Phase 3: Add Production

```
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│      DEV      │  │    STAGING    │  │     PROD      │
│               │  │               │  │               │
│   Feature dev │  │   Testing     │  │   Production  │
│   Debug mode  │  │   Pre-prod    │  │   HA config   │
│   No SLA      │  │   Soft SLA    │  │   Full SLA    │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Air-Gapped Deployment Consideration

Für spätere Air-Gapped Deployments (ADR-025):

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AIR-GAPPED ADAPTATION                                     │
│                                                                                  │
│   Cloud Version (jetzt)         Air-Gapped Version (später)                     │
│   ─────────────────────         ────────────────────────────                    │
│   Cloud Run              →      K8s / K3s on-premise                           │
│   GCP Secret Manager     →      HashiCorp Vault / K8s Secrets                  │
│   Firestore              →      MongoDB / PostgreSQL                           │
│   Cloud Monitoring       →      Prometheus + Grafana                           │
│   GitLab Registry      →      Harbor / Local Registry                        │
│                                                                                  │
│   Terraform modules bleiben gleich, nur Provider/Backend ändern!               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Initial Setup Steps

```bash
# 1. Create Terraform state bucket (einmalig)
gcloud storage buckets create gs://clarissa-terraform-state \
  --project=myk8sproject-207017 \
  --location=europe-west1 \
  --uniform-bucket-level-access

# 2. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  cloudbuild.googleapis.com \
  --project=myk8sproject-207017

# 3. GitLab Container Registry
# Already available at: registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa
# No setup needed - GitLab provides this automatically!

# 4. Initialize Terraform
cd infrastructure/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

---


---

## Local Development Environment

Lokale Entwicklung muss **ohne GCP-Abhängigkeiten** möglich sein.

### Prinzip: Cloud = Optional

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   LOCAL DEV (docker-compose)             CLOUD (GCP)                            │
│   ──────────────────────────             ──────────────                          │
│                                                                                  │
│   clarissa-api (container)        →      Cloud Run Service                      │
│   Firestore Emulator              →      Firestore (real)                       │
│   Ollama (local LLM)              →      Claude API                             │
│   OPM Flow (container)            →      Cloud Run Worker                       │
│   Qdrant (container)              →      Qdrant Cloud / Managed                 │
│                                                                                  │
│   ✅ Kein GCP Account nötig              ⚠️  GCP Credentials nötig              │
│   ✅ Komplett offline                    ⚠️  Internet nötig                      │
│   ✅ Kostenlos                           💰 Pay-per-use                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### docker-compose.yml

```yaml
# docker-compose.yml

version: '3.8'

services:
  # ============== CLARISSA API ==============
  api:
    build:
      context: .
      dockerfile: docker/api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=local
      - LOG_LEVEL=DEBUG
      - FIRESTORE_EMULATOR_HOST=firestore:8080
      - LLM_PROVIDER=ollama
      - OLLAMA_HOST=http://ollama:11434
      - OPM_FLOW_URL=http://opm-flow:8080
      - QDRANT_HOST=http://qdrant:6333
    volumes:
      - ./src:/app/src  # Hot reload
    depends_on:
      - firestore
      - ollama
      - opm-flow
    networks:
      - clarissa-net

  # ============== FIRESTORE EMULATOR ==============
  firestore:
    image: google/cloud-sdk:slim
    command: >
      bash -c "apt-get update && apt-get install -y default-jre &&
               gcloud emulators firestore start --host-port=0.0.0.0:8080"
    ports:
      - "8080:8080"
    networks:
      - clarissa-net

  # ============== LOCAL LLM (OLLAMA) ==============
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - clarissa-net
    # Nach Start: docker exec -it clarissa-ollama-1 ollama pull llama3.2:3b

  # ============== OPM FLOW SIMULATOR ==============
  opm-flow:
    image: opm/opm-simulators:latest
    ports:
      - "8081:8080"
    volumes:
      - ./data/simulations:/data
    networks:
      - clarissa-net

  # ============== VECTOR DATABASE ==============
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - clarissa-net

volumes:
  ollama_data:
  qdrant_data:

networks:
  clarissa-net:
    driver: bridge
```

### Environment Configuration

```python
# src/clarissa/config.py

from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """
    Configuration with local-first defaults.
    Cloud values come from environment variables or .env file.
    """
    
    # Environment
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "DEBUG"
    
    # LLM Configuration
    llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    
    # Database
    firestore_emulator_host: str | None = None  # Set = use emulator
    firestore_project: str = "myk8sproject-207017"
    
    # Simulator
    opm_flow_url: str = "http://localhost:8081"
    
    # Vector Store
    qdrant_host: str = "http://localhost:6333"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

```python
# src/clarissa/llm/factory.py

from clarissa.config import settings

def get_llm():
    """Factory that returns appropriate LLM based on config."""
    
    if settings.llm_provider == "ollama":
        from clarissa.llm.ollama import OllamaAdapter
        return OllamaAdapter(
            host=settings.ollama_host,
            model=settings.ollama_model
        )
    
    elif settings.llm_provider == "anthropic":
        from clarissa.llm.anthropic import AnthropicAdapter
        return AnthropicAdapter(
            api_key=settings.anthropic_api_key
        )
    
    elif settings.llm_provider == "openai":
        from clarissa.llm.openai import OpenAIAdapter
        return OpenAIAdapter(
            api_key=settings.openai_api_key
        )
    
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
```

```python
# src/clarissa/db/factory.py

from clarissa.config import settings

def get_firestore():
    """Factory that handles emulator vs real Firestore."""
    
    import os
    from google.cloud import firestore
    
    if settings.firestore_emulator_host:
        # Use emulator
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host
    
    return firestore.Client(project=settings.firestore_project)
```

### Quick Start (Local)

```bash
# 1. Clone & Setup
git clone git@gitlab.com:wolfram_laube/blauweiss_llc/clarissa.git
cd clarissa
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Pull local LLM model (first time only, ~2GB)
docker exec -it clarissa-ollama-1 ollama pull llama3.2:3b

# 4. Verify
curl http://localhost:8000/health
# → {"status": "healthy", "environment": "local"}

# 5. Develop with hot-reload
# Edit src/ → changes apply automatically
```

### .env.example

```bash
# .env.example - Copy to .env for local development

# Environment
ENVIRONMENT=local
LOG_LEVEL=DEBUG

# LLM - Local by default
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Uncomment for cloud LLM:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Database - Emulator by default
FIRESTORE_EMULATOR_HOST=localhost:8080
FIRESTORE_PROJECT=myk8sproject-207017

# Simulator
OPM_FLOW_URL=http://localhost:8081

# Vector Store
QDRANT_HOST=http://localhost:6333
```

### Switching Between Local and Cloud

```bash
# Local (default)
docker-compose up
# → Uses Ollama, Firestore Emulator, everything local

# Local + Cloud LLM (for testing Claude responses)
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-... docker-compose up
# → Uses Claude API, but Firestore still local

# Against Dev Environment (careful!)
ENVIRONMENT=dev \
FIRESTORE_EMULATOR_HOST= \
LLM_PROVIDER=anthropic \
ANTHROPIC_API_KEY=sk-... \
python -m clarissa.api
# → Uses real Firestore, real Claude
```

## Summary

| Component | Decision | Rationale |
|-----------|----------|-----------|
| **IaC** | Terraform | Industry standard, reusable modules |
| **Deployment** | GitLab CI → Cloud Run | Simple, serverless, scale-to-zero |
| **Secrets** | GCP Secret Manager | Native, no extra infrastructure |
| **Environments** | Dev only (start) | Minimize cost, add later |
| **GitOps** | GitLab CI (no ArgoCD) | Small team, keep it simple |
| **Container Registry** | GitLab Registry | Already have it, CI-native |
| **State Storage** | GCS Bucket | Reliable, supports locking |

---

## Next Steps

1. [ ] Setup local dev (docker-compose up)
2. [ ] Create Terraform state bucket
3. [ ] Enable GCP APIs
4. [x] GitLab Registry (already have it!)
5. [ ] Implement Terraform modules
6. [ ] Add CI pipeline jobs
7. [ ] Deploy "Hello World" to Cloud Run
8. [ ] Verify secrets injection works

---

## References

- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [GitLab CI/CD for GCP](https://docs.gitlab.com/ee/ci/cloud_deployment/)
