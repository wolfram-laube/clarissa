# ADR-015: LLM-Powered CI/CD Notification System

## Status
**Accepted** (Implemented 2026-01-17)

!!! success "Implementation Complete"
    This ADR has been implemented. See [BENCHMARK_HOWTO.md](../ci/BENCHMARK_HOWTO.md) for operational documentation.

## Context

The CLARISSA project operates a 12-runner CI/CD matrix (4 machines × 3 executor types: Shell, Docker, Kubernetes). Benchmark pipelines generate performance data that needs to be communicated to stakeholders.

**Challenges with traditional notification approaches:**

1. **Static Templates**: Pre-written email templates cannot adapt to varying benchmark results
2. **Data Interpretation**: Raw numbers require human analysis to extract insights
3. **Language Barriers**: International team members prefer different languages
4. **Context Loss**: Automated reports lack the narrative that explains *why* results matter

**We need a system that can:**

- Analyze benchmark data and extract key insights automatically
- Generate human-readable summaries in multiple languages
- Adapt tone and content based on results (e.g., highlight anomalies)
- Integrate seamlessly with existing CI/CD infrastructure

## Decision

Implement an **LLM-Powered Email Generation System** in GitLab CI/CD that:

1. **Collects** benchmark timing data from all 12 runner jobs via GitLab API
2. **Analyzes** results using OpenAI GPT-4o-mini or Anthropic Claude-3.5-Haiku
3. **Generates** contextual email summaries in the user's preferred language
4. **Creates** Gmail drafts with benchmark charts as attachments

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitLab CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ benchmark-   │  │ benchmark-   │  │ benchmark-   │   × 12      │
│  │ mac-shell    │  │ mac-docker   │  │ mac-k8s      │   jobs       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           ▼                                         │
│                 ┌─────────────────┐                                 │
│                 │ benchmark-report │  ← Collects data, generates   │
│                 │                  │    charts (matplotlib)         │
│                 └────────┬────────┘                                 │
│                          │                                          │
│                          ▼                                          │
│                 ┌─────────────────┐                                 │
│                 │    Artifacts    │                                 │
│                 │ • benchmark_    │                                 │
│                 │   data.json     │                                 │
│                 │ • *.png charts  │                                 │
│                 └────────┬────────┘                                 │
│                          │                                          │
│                          ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              gmail:benchmark-report                            │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  1. Load benchmark_data.json                            │  │ │
│  │  │  2. Select LLM provider (OPENAI / ANTHROPIC)            │  │ │
│  │  │  3. Select language (de / en / es / fr)                 │  │ │
│  │  │  4. Generate prompt with benchmark data                 │  │ │
│  │  │  5. Call LLM API                                        │  │ │
│  │  │  6. Attach PNG charts                                   │  │ │
│  │  │  7. Create Gmail draft via OAuth2                       │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│                 ┌─────────────────┐                                 │
│                 │   Gmail Draft   │  ← Ready for review & send     │
│                 │   + 4 PNG       │                                 │
│                 │   attachments   │                                 │
│                 └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Configuration Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `SEND_BENCHMARK_EMAIL` | - | `true` | Enable email generation |
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic` | LLM backend selection |
| `EMAIL_LANGUAGE` | `de` | `de`, `en`, `es`, `fr` | Output language |

### LLM Provider Configuration

**OpenAI (Default)**
```yaml
Model: gpt-4o-mini
Max Tokens: 500
Temperature: 0.7
Cost: ~$0.001 per email
```

**Anthropic (Alternative)**
```yaml
Model: claude-3-5-haiku-20241022
Max Tokens: 500
Cost: ~$0.001 per email
```

### Prompt Engineering

The LLM receives structured benchmark data and language-specific instructions:

```python
prompt = f"""Schreibe eine kurze, professionelle E-Mail auf Deutsch...

Benchmark-Daten:
{json.dumps(benchmark_data, indent=2)}

Anforderungen:
- Beginne mit "Hallo Wolfram,"
- Fasse die wichtigsten Erkenntnisse zusammen 
  (schnellster/langsamster Runner, Vergleich der Executors)
- Erwähne dass 4 Grafiken als Anhänge dabei sind
- Halte es kurz und informativ (max 150 Wörter)
- Ende mit "Grüße, CLARISSA CI/CD Pipeline"
"""
```

### Multilingual Support

| Code | Language | Greeting | Closing |
|------|----------|----------|---------|
| `de` | Deutsch | "Hallo Wolfram," | "Grüße, CLARISSA CI/CD Pipeline" |
| `en` | English | "Hi Wolfram," | "Best regards, CLARISSA CI/CD Pipeline" |
| `es` | Español | "Hola Wolfram," | "Saludos, CLARISSA CI/CD Pipeline" |
| `fr` | Français | "Bonjour Wolfram," | "Cordialement, CLARISSA CI/CD Pipeline" |

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

## Implementation

### File Structure

```
scripts/ci/
└── send_benchmark_email.py    # Main script (200 LOC)

.gitlab/
├── benchmark.yml              # 12 benchmark jobs + report generator
└── gmail-drafts.yml           # Email generation job
```

### Script: `send_benchmark_email.py`

Key components:

1. **Language Configuration**: `LANGUAGE_CONFIG` dict with prompts per language
2. **LLM Functions**: `generate_email_with_openai()`, `generate_email_with_anthropic()`
3. **Fallback**: Static template if LLM unavailable
4. **Email Construction**: MIME multipart with UTF-8 text + PNG attachments
5. **Gmail API**: OAuth2 token refresh + draft creation

### CI Job: `gmail:benchmark-report`

```yaml
gmail:benchmark-report:
  stage: deploy
  needs:
    - job: benchmark-report
      artifacts: true
  variables:
    LLM_PROVIDER: "openai"
    EMAIL_LANGUAGE: "de"
  script:
    - pip3 install requests openai anthropic
    - python3 scripts/ci/send_benchmark_email.py
```

## Alternatives Considered

### 1. Static Email Templates
- **Rejected**: Cannot adapt to varying results
- No insight extraction, just raw numbers

### 2. Rule-Based Text Generation
- **Rejected**: Requires extensive if/else logic
- Difficult to maintain across languages
- Cannot handle unexpected patterns

### 3. Slack/Teams Webhooks Only
- **Partially Accepted**: Could add later as complement
- Email preferred for formal reporting
- Attachments easier in email

### 4. External Email Service (SendGrid, Mailgun)
- **Rejected**: Additional dependency and cost
- Gmail integration already available via OAuth

## Consequences

### Positive

- **Contextual Insights**: LLM extracts meaning from data, not just numbers
- **Multilingual**: Easy to add more languages (just add to `LANGUAGE_CONFIG`)
- **Low Cost**: ~$0.001 per email with GPT-4o-mini
- **Graceful Degradation**: Falls back to static template if LLM fails
- **Extensible**: Same pattern can be used for other CI notifications

### Negative

- **External Dependency**: Requires OpenAI or Anthropic API
- **Latency**: LLM call adds 2-5 seconds to job runtime
- **Non-Deterministic**: Same data may produce slightly different text
- **API Key Management**: Must secure keys in CI variables

### Risks

| Risk | Mitigation |
|------|------------|
| LLM API failure | Fallback to static template |
| Hallucinated insights | Prompt constrains output format |
| Cost overrun | gpt-4o-mini is very cheap (~$0.001) |
| Rate limiting | Single email per pipeline run |

## Required CI Variables

| Variable | Secret | Description |
|----------|--------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API access |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API access (optional) |
| `GMAIL_CLIENT_ID` | Yes | Gmail OAuth client ID |
| `GMAIL_CLIENT_SECRET` | Yes | Gmail OAuth client secret |
| `GMAIL_REFRESH_TOKEN` | Yes | Gmail OAuth refresh token |

## Future Extensions

1. **Slack Integration**: Post summary to `#ci-notifications` channel
2. **Anomaly Detection**: Highlight significant performance regressions
3. **Trend Analysis**: Compare with previous N pipelines
4. **Custom Recipients**: Configure email recipients per project
5. **More Languages**: Add Japanese, Chinese, Arabic support

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Gmail API - Creating Drafts](https://developers.google.com/gmail/api/guides/drafts)
- [ADR-014: LLM Document Merge](ADR-014-llm-document-merge.md) - Related LLM usage in CI

---

*Accepted: 2026-01-17*
*Author: Wolfram Laube*
