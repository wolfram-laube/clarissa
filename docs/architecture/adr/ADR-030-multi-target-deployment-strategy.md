# ADR-030: Multi-Target Deployment Strategy

| Status | Proposed |
|--------|----------|
| Date | 2026-01-25 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-029 (Deployment & Infrastructure), ADR-024 (Core System) |

---

## Context

CLARISSA muss auf verschiedenen Plattformen deploybar sein:

1. **Entwickler-Laptop** → Schnelles Iterieren, offline-fähig
2. **Lokales Kubernetes** → Testen vor Air-Gap-Deployment
3. **GCP Cloud** → SaaS, Demos, schneller Start
4. **Air-Gapped On-Prem** → Enterprise-Kunden (Öl, Bank, Militär)

Wir brauchen eine einheitliche Deployment-Strategie, die alle Targets mit minimalem Code-Duplizierung unterstützt.

---

## Decision

### Terraform Multi-Environment Architecture

```
infrastructure/
└── terraform/
    ├── modules/                    # Wiederverwendbare Module
    │   ├── clarissa-api/           # API Service Abstraktion
    │   ├── clarissa-worker/        # Worker Service Abstraktion
    │   ├── database/               # DB Abstraktion
    │   ├── secrets/                # Secrets Abstraktion
    │   └── monitoring/             # Observability Abstraktion
    │
    └── environments/
        ├── local-docker/           # docker-compose (kein Terraform)
        ├── local-k8s/              # K3s/minikube
        ├── gcp/                    # Google Cloud
        └── airgapped/              # On-Prem Kubernetes
```

### Deployment Matrix

```
┌─────────────────┬────────────────┬──────────────┬─────────────┬──────────────┐
│ Component       │ local-docker   │ local-k8s    │ gcp         │ airgapped    │
├─────────────────┼────────────────┼──────────────┼─────────────┼──────────────┤
│ Orchestration   │ docker-compose │ K3s/minikube │ Cloud Run   │ K8s          │
│ Database        │ Firestore Emu  │ MongoDB      │ Firestore   │ PostgreSQL   │
│ Secrets         │ .env file      │ K8s Secrets  │ Secret Mgr  │ Vault        │
│ LLM             │ Ollama         │ Ollama       │ Claude API  │ Ollama/vLLM  │
│ Vector DB       │ Qdrant         │ Qdrant       │ Qdrant      │ Qdrant       │
│ Registry        │ local build    │ local/GitLab │ GitLab      │ Harbor       │
│ Monitoring      │ logs only      │ Prometheus   │ Cloud Mon.  │ Prometheus   │
│ Internet        │ ❌ optional    │ ❌ optional  │ ✅ required │ ❌ none      │
└─────────────────┴────────────────┴──────────────┴─────────────┴──────────────┘
```

### Provider Strategy

```hcl
# Abstraktion über Terraform Providers

# GCP Environment
provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# Kubernetes Environments (local-k8s, airgapped)
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Air-Gapped additions
provider "vault" {
  address = var.vault_address
}
```

### Module Interface (einheitlich für alle Targets)

```hcl
# Jedes Modul hat dasselbe Interface, unterschiedliche Implementation

module "clarissa_api" {
  source = "./modules/clarissa-api/${var.target}"
  
  # Einheitliche Variablen
  name        = "clarissa-api"
  image       = var.api_image
  replicas    = var.api_replicas
  
  environment = {
    LOG_LEVEL    = var.log_level
    LLM_PROVIDER = var.llm_provider
  }
  
  secrets = {
    ANTHROPIC_API_KEY = var.anthropic_api_key
  }
  
  resources = {
    cpu    = "1"
    memory = "1Gi"
  }
}
```

---

## Implementation Phases

### Phase 1: GCP (jetzt)
- Cloud Run für Services
- Secret Manager für Credentials
- Firestore für Datenbank
- GitLab Registry für Images

### Phase 2: Local K8s (nächste Woche)
- K3s/minikube Support
- Kubernetes Provider
- Helm Charts optional
- MongoDB statt Firestore

### Phase 3: Air-Gapped (Q2 2026)
- Vault Integration
- Harbor Registry
- Offline LLM (Ollama/vLLM)
- PostgreSQL

---

## Directory Structure (Final)

```
infrastructure/
├── terraform/
│   ├── modules/
│   │   ├── clarissa-api/
│   │   │   ├── gcp/
│   │   │   │   └── main.tf      # Cloud Run implementation
│   │   │   ├── k8s/
│   │   │   │   └── main.tf      # Kubernetes Deployment
│   │   │   ├── variables.tf     # Shared interface
│   │   │   └── outputs.tf       # Shared outputs
│   │   │
│   │   ├── database/
│   │   │   ├── gcp/             # Firestore
│   │   │   └── k8s/             # MongoDB/PostgreSQL
│   │   │
│   │   └── secrets/
│   │       ├── gcp/             # Secret Manager
│   │       └── k8s/             # K8s Secrets / Vault
│   │
│   ├── environments/
│   │   ├── gcp/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── backend.tf       # GCS state
│   │   │   └── terraform.tfvars.example
│   │   │
│   │   ├── local-k8s/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── backend.tf       # Local state
│   │   │
│   │   └── airgapped/
│   │       └── ... (später)
│   │
│   └── README.md
│
├── k8s/                          # Raw K8s manifests (alternative zu Terraform)
│   ├── base/
│   └── overlays/
│       ├── local/
│       └── production/
│
└── scripts/
    ├── setup-gcp.sh
    ├── setup-local-k8s.sh
    └── bundle-airgapped.sh
```

---

## Usage

```bash
# GCP Deployment
cd infrastructure/terraform/environments/gcp
terraform init
terraform plan
terraform apply

# Local K8s Deployment  
cd infrastructure/terraform/environments/local-k8s
terraform init
terraform plan
terraform apply

# Air-Gapped (mit gebundelten Providern)
cd infrastructure/terraform/environments/airgapped
terraform init -plugin-dir=/path/to/bundle
terraform apply
```

---

## Consequences

### Positive
- Ein Codebase für alle Deployment-Targets
- Klare Abstraktion durch Module
- Testbar: local-k8s validiert air-gapped Setup
- Flexibel: Neue Targets einfach hinzufügbar

### Negative
- Mehr initiale Komplexität
- Module-Interfaces müssen stabil bleiben
- Testing für alle Targets nötig

### Risks
- Provider-Versionen zwischen Targets divergieren
- Module-Interface wird zu generisch

---

## References

- ADR-029: Deployment & Infrastructure Strategy
- [Terraform Modules Best Practices](https://developer.hashicorp.com/terraform/language/modules/develop)
- [Multi-Environment Terraform](https://developer.hashicorp.com/terraform/tutorials/modules/pattern-module-creation)
