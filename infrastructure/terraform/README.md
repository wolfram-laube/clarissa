# CLARISSA Infrastructure

Terraform-based infrastructure supporting multiple deployment targets.

## Deployment Targets

| Target | Tool | Use Case |
|--------|------|----------|
| `local-docker` | docker-compose | Development (no Terraform) |
| `local-k8s` | Terraform + K8s | Pre-air-gap testing |
| `gcp` | Terraform + GCP | Cloud/SaaS deployment |
| `airgapped` | Terraform + K8s | Enterprise on-prem |

## Quick Start

### Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or: sudo apt install terraform  # Linux

# GCP Authentication (for gcp target)
gcloud auth application-default login
```

### GCP Deployment

```bash
cd terraform/environments/gcp

# First time: create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize
terraform init

# Preview changes
terraform plan

# Apply (creates real resources!)
terraform apply

# Destroy when done
terraform destroy
```

### Local K8s Deployment

```bash
# Start K3s/minikube first
k3d cluster create clarissa
# or: minikube start

cd terraform/environments/local-k8s
terraform init
terraform plan
terraform apply
```

## Directory Structure

```
infrastructure/
└── terraform/
    ├── modules/                 # Reusable modules
    │   ├── clarissa-api/
    │   │   ├── gcp/            # Cloud Run implementation
    │   │   └── k8s/            # Kubernetes implementation
    │   ├── database/
    │   └── secrets/
    │
    └── environments/           # Environment-specific configs
        ├── gcp/                # Google Cloud Platform
        ├── local-k8s/          # Local Kubernetes (K3s/minikube)
        └── airgapped/          # Air-gapped on-prem (future)
```

## Module Interface

All modules share a consistent interface:

```hcl
module "clarissa_api" {
  source = "../../modules/clarissa-api/gcp"  # or /k8s
  
  name        = "clarissa-api"
  image       = var.api_image
  environment = { ... }
  secrets     = { ... }
  resources   = { cpu = "1", memory = "1Gi" }
}
```

## State Management

| Environment | Backend | Location |
|-------------|---------|----------|
| gcp | GCS | gs://clarissa-terraform-state/ |
| local-k8s | local | ./terraform.tfstate |
| airgapped | local | ./terraform.tfstate (bundled) |

## Related Documentation

- [ADR-029: Deployment & Infrastructure Strategy](../../docs/architecture/adr/ADR-029-deployment-infrastructure-strategy.md)
- [ADR-030: Multi-Target Deployment Strategy](../../docs/architecture/adr/ADR-030-multi-target-deployment-strategy.md)
- [Local Development Guide](../../docs/development/local-setup.md)
