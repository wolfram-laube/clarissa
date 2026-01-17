# GitLab Runner Benchmark Guide

## Overview

The CLARISSA project maintains a 12-runner CI/CD matrix across 4 machines with 3 executor types each. This guide documents how to run performance benchmarks and interpret results.

## Runner Matrix

| Machine | Shell | Docker | Kubernetes |
|---------|-------|--------|------------|
| Mac #1 | `mac-group-shell` | `mac-docker` | `mac-k8s` |
| Mac #2 | `mac2-shell` | `mac2-docker` | `mac2-k8s` |
| Linux Yoga | `linux-shell` | `linux-docker` | `linux-k8s` |
| GCP VM | `gcp-shell` | `gcp-docker` | `gcp-k8s` |

## Running Benchmarks

### Via GitLab UI

1. Navigate to **CI/CD → Pipelines**
2. Click **"Run pipeline"** on `main` branch
3. Wait for pipeline creation
4. Find benchmark jobs (all prefixed with `benchmark-`)
5. Click the **▶ Play** button on each benchmark job
6. Jobs run in parallel across all available runners

### Via GitLab API

```bash
# Set your token
export GITLAB_TOKEN="glpat-..."
export PROJECT_ID="77260390"

# 1. Create a new pipeline
PIPELINE_ID=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --request POST \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipeline?ref=main" | \
  jq -r '.id')

echo "Pipeline created: $PIPELINE_ID"

# 2. List benchmark jobs
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines/$PIPELINE_ID/jobs" | \
  jq '.[] | select(.name | startswith("benchmark-")) | {id, name, status}'

# 3. Trigger all benchmark jobs
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines/$PIPELINE_ID/jobs" | \
  jq -r '.[] | select(.name | startswith("benchmark-")) | .id' | \
  while read JOB_ID; do
    curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      --request POST \
      "https://gitlab.com/api/v4/projects/$PROJECT_ID/jobs/$JOB_ID/play" | \
      jq '{name, status}'
  done

# 4. Monitor status
watch -n 5 "curl -s --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \
  'https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines/$PIPELINE_ID/jobs' | \
  jq '.[] | select(.name | startswith(\"benchmark-\")) | {name, status, duration}'"
```

### Via Python Script

```bash
# Generate report with visualizations
python scripts/benchmark_report.py --pipeline-id <PIPELINE_ID>
```

## Benchmark Test Specification

Each benchmark job executes:

1. **CPU Test**: Count primes up to 100,000
   ```python
   sum(1 for n in range(2,100000) if all(n%i for i in range(2,int(n**0.5)+1)))
   ```

2. **Disk Test**: 50MB sequential write
   ```bash
   dd if=/dev/zero of=/tmp/test bs=1M count=50
   ```

## Interpreting Results

### Expected Performance Ranges

| Executor | Fast | Normal | Slow |
|----------|------|--------|------|
| Shell | < 8s | 8-15s | > 15s |
| Docker | < 15s | 15-30s | > 30s |
| Kubernetes | < 20s | 20-40s | > 40s |

### Common Issues

| Symptom | Possible Cause | Resolution |
|---------|----------------|------------|
| Shell slow | Resource contention | Check other processes |
| Docker slow | Image pull | Pre-pull `python:3.11-slim` |
| K8s failed | No cluster | Configure kubeconfig |
| All slow | Network latency | Check GitLab connectivity |

## Report Generation

The `scripts/benchmark_report.py` script generates:

- `BENCHMARK_REPORT.md` - Markdown report with visualizations
- `benchmark_data.json` - Raw data for archival
- `benchmark_*.png` - Chart visualizations

### Output Location

Reports are uploaded to:
- **GitLab Pages**: `https://wolfram_laube.gitlab.io/blauweiss_llc/irena/benchmarks/`
- **Google Drive**: Shared folder `CLARISSA/Benchmarks/`

## Version History

| Version | Date | Pipeline | Notes |
|---------|------|----------|-------|
| 1.0.0 | 2026-01-17 | 2268913615 | Initial 12-runner matrix |

---

*Last updated: 2026-01-17*
