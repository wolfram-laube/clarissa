# LLM Relay System

CLARISSA supports two LLM-to-LLM communication modes for collaborative development.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLARISSA LLM Relay                          │
│                                                                 │
│   Claude (Operator)                                             │
│   ├── Primary development agent                                 │
│   ├── Code implementation                                       │
│   └── GitLab integration                                        │
│         │                                                       │
│         ├──────────────┬──────────────────────┐                │
│         ▼              ▼                      ▼                │
│   ┌──────────┐   ┌──────────────┐   ┌────────────────┐        │
│   │ relay.py │   │claude_relay.py│   │  (Future)     │        │
│   │ OpenAI   │   │  Anthropic   │   │  Local LLM    │        │
│   └────┬─────┘   └──────┬───────┘   └───────────────┘        │
│        ▼                ▼                                      │
│   ┌──────────┐   ┌──────────────┐                             │
│   │  IRENA   │   │    IRENA     │                             │
│   │ (GPT-4o) │   │   (Claude)   │                             │
│   └──────────┘   └──────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Option 1: OpenAI Relay (relay.py)

Uses ChatGPT/GPT-4o as IRENA consultant.

**Pros:**
- Different model perspective (diversity)
- Good for second opinions

**Cons:**
- Slower (~15-30 seconds)
- File-based handoff process

**Usage:**
```bash
export OPENAI_API_KEY="sk-proj-..."
python scripts/relay.py --process
```

## Option 2: Claude Relay (claude_relay.py)

Uses another Claude instance as IRENA consultant.

**Pros:**
- Instant response (~5 seconds)
- Direct function calls possible
- Same reasoning quality

**Cons:**
- Same model biases
- No external perspective

**Usage:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Direct question
python scripts/claude_relay.py --question "What are aquifer keywords?" --repo

# Process handoff file
python scripts/claude_relay.py --process
```

**As library:**
```python
from scripts.claude_relay import ask_irena

response = ask_irena(
    question="Review this entity extraction logic",
    context=code_snippet,
    include_repo=True
)
```

## Handoff Format

Both systems use the same handoff format in `handoffs/`:

```markdown
# 🔄 LLM Handoff

**Generated:** 2026-01-04 15:00
**From:** Claude (Operator)
**To:** IRENA (Consultant)

---

## Context
[Description of current work]

## Question
[Specific question or review request]

## Code References
[Mention files like taxonomy.json, intent.py for auto-inclusion]
```

## Environment Variables

| Variable | Required For | Description |
|----------|--------------|-------------|
| `OPENAI_API_KEY` | relay.py | OpenAI API key |
| `ANTHROPIC_API_KEY` | claude_relay.py | Anthropic API key |

GitLab token is embedded in scripts (project-specific).

## CI/CD Integration

For automated relay on push, add to `.gitlab-ci.yml`:

```yaml
relay:
  stage: deploy
  rules:
    - changes: [handoffs/handoff_to_irena.md]
  script:
    - pip install openai  # or nothing for claude_relay
    - python scripts/relay.py --process  # or claude_relay.py
  variables:
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    # or ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
```