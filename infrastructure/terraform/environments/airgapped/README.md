# CLARISSA Infrastructure - Air-Gapped Environment

> 🚧 **PLACEHOLDER** - To be implemented in Phase 3 (Q2 2026)

## Overview

This environment supports deployment to air-gapped (no internet) data centers.

## Key Differences from local-k8s

| Component | local-k8s | airgapped |
|-----------|-----------|-----------|
| Secrets | K8s Secrets | HashiCorp Vault |
| Registry | GitLab/local | Harbor (on-prem) |
| LLM | Ollama | Ollama/vLLM |
| Database | MongoDB | PostgreSQL |
| Monitoring | Basic | Prometheus + Grafana |

## Prerequisites

1. **Pre-bundled Terraform providers**
   ```bash
   terraform providers mirror ./providers
   ```

2. **Pre-pulled container images** (via Harbor or tarball)

3. **Vault instance** with PKI and secrets engine configured

## Deployment (Future)

```bash
# Initialize with bundled providers
terraform init -plugin-dir=./providers

# Apply
terraform apply
```

## Bundle Creation Script

See `scripts/bundle-airgapped.sh` for creating the deployment bundle.

## Related

- ADR-030: Multi-Target Deployment Strategy
- [HashiCorp Vault Provider](https://registry.terraform.io/providers/hashicorp/vault)
