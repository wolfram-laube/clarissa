# CLARISSA Infrastructure Credentials

> ⚠️ **PRIVATE** - Dieses Dokument enthält echte Credentials.
> Nur möglich weil das Repository privat ist.

## GitLab

| Key | Value |
|-----|-------|
| Project ID | `77260390` |
| Project URL | https://gitlab.com/wolfram_laube/blauweiss_llc/irena |
| PAT (Personal Access Token) | `glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt` |
| Default Branch | `main` |

### API Beispiele
```bash
# List commits
curl -H "PRIVATE-TOKEN: glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt" \
  "https://gitlab.com/api/v4/projects/77260390/repository/commits"

# Fetch file
curl -H "PRIVATE-TOKEN: glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt" \
  "https://gitlab.com/api/v4/projects/77260390/repository/files/README.md/raw?ref=main"
```

---

## LLM APIs

### OpenAI (ChatGPT / IRENA)
| Key | Value |
|-----|-------|
| API Key | `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` |
| Model | `gpt-4o` |
| Use Case | IRENA Consultant (relay.py) |

### Anthropic (Claude-to-Claude)
| Key | Value |
|-----|-------|
| API Key | `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` |
| Model | `claude-3-5-sonnet-20241022` |
| Use Case | IRENA Consultant (claude_relay.py) |
| Status | ⚠️ Needs credits on account |

---

## GitLab CI Variables

Diese Werte sind auch als CI Variables gesetzt (Settings → CI/CD → Variables):

| Variable | Masked | Purpose |
|----------|--------|---------|
| `GITLAB_TOKEN` | ❌ | CI push-back to repo |
| `OPENAI_API_KEY` | ✅ | relay.py (ChatGPT) |
| `ANTHROPIC_API_KEY` | ✅ | claude_relay.py (Claude) |
| `GOOGLE_DRIVE_FOLDER_ID` | ❌ | Sync packages |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | ❌ | GDrive API |

---

## Quick Reference für Claude

```bash
# Environment Setup
export GITLAB_TOKEN="glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
export GITLAB_PROJECT_ID="77260390"
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
```

---

*Last updated: 2026-01-04*