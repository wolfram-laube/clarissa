# GitLab Runner Benchmark Guide

## Overview

The CLARISSA project maintains a 12-runner CI/CD matrix across 4 machines with 3 executor types each. This guide documents how to run performance benchmarks, generate reports, and configure automated email notifications.

## Runner Matrix

| Machine | Shell | Docker | Kubernetes |
|---------|-------|--------|------------|
| Mac #1 | `mac-group-shell` | `mac-docker` | `mac-k8s` |
| Mac #2 | `mac2-shell` | `mac2-docker` | `mac2-k8s` |
| Linux Yoga | `linux-shell` | `linux-docker` | `linux-k8s` |
| GCP VM | `gcp-shell` | `gcp-docker` | `gcp-k8s` |

## Running Benchmarks

### Quick Start (Full Pipeline with Email)

```bash
# Run all 12 benchmarks + report + email notification
curl --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  "https://gitlab.com/api/v4/projects/77260390/pipeline" \
  --data '{
    "ref": "main",
    "variables": [
      {"key": "BENCHMARK", "value": "true"},
      {"key": "SEND_BENCHMARK_EMAIL", "value": "true"},
      {"key": "EMAIL_LANGUAGE", "value": "en"}
    ]
  }'
```

### Via GitLab UI

1. Navigate to **CI/CD → Pipelines**
2. Click **"Run pipeline"** on `main` branch
3. Add variables:
   - `BENCHMARK` = `true`
   - `SEND_BENCHMARK_EMAIL` = `true` (optional)
   - `EMAIL_LANGUAGE` = `de` / `en` / `es` / `fr` (optional)
4. Click **Run pipeline**
5. Manually trigger benchmark jobs via ▶ Play button

### Via GitLab API

```bash
export GITLAB_TOKEN="glpat-..."
export PROJECT_ID="77260390"

# 1. Create pipeline
PIPELINE_ID=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --request POST \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipeline?ref=main" | jq -r '.id')

# 2. Trigger all benchmark jobs
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines/$PIPELINE_ID/jobs" | \
  jq -r '.[] | select(.name | startswith("benchmark-")) | .id' | \
  while read JOB_ID; do
    curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      --request POST \
      "https://gitlab.com/api/v4/projects/$PROJECT_ID/jobs/$JOB_ID/play"
  done
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

## Automated Report Generation

### The `benchmark-report` Job

After all 12 benchmark jobs complete, the `benchmark-report` job automatically:

1. Collects timing data via GitLab API
2. Generates 4 PNG visualizations:
   - `benchmark_by_machine.png` - Comparison by machine
   - `benchmark_by_executor.png` - Comparison by executor type
   - `benchmark_detailed.png` - All 12 runners horizontal bar chart
   - `benchmark_heatmap.png` - Machine × Executor heatmap
3. Creates `benchmark_data.json` with raw data
4. Creates `BENCHMARK_REPORT.md` summary

### Output Artifacts

Reports are stored in `docs/ci/benchmarks/` and uploaded to:
- **GitLab Artifacts**: Available for 7 days
- **Google Drive**: `CLARISSA/Benchmarks/` (via `gdrive:upload-benchmark` job)

## LLM-Powered Email Notifications

### Overview

The `gmail:benchmark-report` job creates Gmail drafts with AI-generated summaries of benchmark results.

### Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEND_BENCHMARK_EMAIL` | - | Set to `true` to enable email generation |
| `LLM_PROVIDER` | `openai` | LLM backend: `openai` or `anthropic` |
| `EMAIL_LANGUAGE` | `de` | Email language: `de`, `en`, `es`, `fr` |

### Supported Languages

| Code | Language | Greeting | Closing |
|------|----------|----------|---------|
| `de` | Deutsch | "Hallo Wolfram," | "Grüße, CLARISSA CI/CD Pipeline" |
| `en` | English | "Hi Wolfram," | "Best regards, CLARISSA CI/CD Pipeline" |
| `es` | Español | "Hola Wolfram," | "Saludos, CLARISSA CI/CD Pipeline" |
| `fr` | Français | "Bonjour Wolfram," | "Cordialement, CLARISSA CI/CD Pipeline" |

### LLM Providers

**OpenAI (default)**
- Model: `gpt-4o-mini`
- Requires: `OPENAI_API_KEY` CI variable

**Anthropic**
- Model: `claude-3-5-haiku-20241022`
- Requires: `ANTHROPIC_API_KEY` CI variable

### Example Output (English)

```
Hi Wolfram,

The GitLab CI/CD Benchmark Report for the pipeline run on January 17, 2026, 
shows that the fastest job was executed on the "Linux Yoga" machine using 
the "shell" executor, completing in just 5.7 seconds. Conversely, the slowest 
was the "benchmark-mac-docker" on "Mac #1," taking 46.9 seconds. Overall, 
the "shell" executor demonstrated the best performance across all machines.

I have attached four charts that provide a visual comparison of the 
performance metrics.

Best regards,  
CLARISSA CI/CD Pipeline
```

### Email Features

- **LLM-Generated Content**: Analyzes benchmark data and highlights key findings
- **Multilingual**: Supports German, English, Spanish, French
- **PNG Attachments**: All 4 benchmark charts included
- **UTF-8 Support**: Proper encoding for umlauts and special characters
- **Fallback**: Static template if LLM unavailable

### Script Location

`scripts/ci/send_benchmark_email.py`

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
| Email empty | No benchmark data | Ensure `benchmark-report` ran first |
| LLM failed | Missing API key | Check CI variables |

## Required CI Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `OPENAI_API_KEY` | OpenAI API access | LLM email (openai) |
| `ANTHROPIC_API_KEY` | Anthropic API access | LLM email (anthropic) |
| `GMAIL_CLIENT_ID` | Gmail OAuth | Email drafts |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth | Email drafts |
| `GMAIL_REFRESH_TOKEN` | Gmail OAuth | Email drafts |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | GCP service account | Google Drive upload |
| `GOOGLE_DRIVE_FOLDER_ID` | Drive folder ID | Google Drive upload |

## Version History

| Version | Date | Pipeline | Notes |
|---------|------|----------|-------|
| 2.0.0 | 2026-01-17 | 2269221874 | LLM email, multilingual, 12/12 runners |
| 1.1.0 | 2026-01-17 | 2269209643 | Automated report generation |
| 1.0.0 | 2026-01-17 | 2268913615 | Initial 12-runner matrix |

---

*Last updated: 2026-01-17*
