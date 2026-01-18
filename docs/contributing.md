# Contributing to CLARISSA

## Quick Start

**New here? Start with these:**

1. **[Workflow Slides](guides/contributing/index.html)** - Interactive 5-minute intro
2. **[Issue Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards)** - Pick a task from the "Ready" column
3. **[Project Management Guide](guides/project-management.md)** - Full reference

## Your First Contribution

```bash
# 1. Pick an issue from the board, e.g. #42
#    Move it to "In Progress"

# 2. Create a branch (issue number first!)
git checkout -b 42-short-description

# 3. Make changes, commit with issue reference
git commit -m "feat: add feature X #42"

# 4. Push and create MR
git push -u origin 42-short-description
# → Click the MR link GitLab shows you
# → Add "Closes #42" in MR description

# 5. Wait for review, then merge
#    Issue closes automatically!
```

## Workflow Cheatsheet

| Step | Command/Action |
|------|----------------|
| Find work | [Issue Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) → "Ready" column |
| Start work | `git checkout -b 42-description` |
| Commit | `git commit -m "type: message #42"` |
| Push | `git push -u origin 42-description` |
| Close issue | Add `Closes #42` in MR description |

**Commit types:** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`

## Labels We Use

| Label | Meaning |
|-------|---------|
| `type::feature` | New functionality |
| `type::bug` | Something broken |
| `type::docs` | Documentation |
| `type::task` | General work |
| `priority::high` | Do this first |
| `workflow::ready` | Ready to pick up |
| `workflow::in-progress` | Someone's working on it |
| `workflow::done` | Completed and merged |

Full label reference: [Project Management Guide](guides/project-management.md#label-system)

---

## Development Setup

```bash
# Clone and install
git clone git@gitlab.com:wolfram_laube/blauweiss_llc/irena.git
cd irena
pip install -e ".[dev]"

# Run tests
pytest -q

# Run CLI
python -m clarissa demo
```

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks run CLI snapshot tests and fast unit tests before each commit.

To refresh snapshots: `make update-snapshots`

---

## Code Guidelines

### ADR Discipline

If a change alters behavior, responsibilities, authority, or safety boundaries:
- Reference an existing ADR, or
- Introduce a new ADR in `docs/architecture/adr/`

### Boundaries

- `src/clarissa/` must not import from `experiments/`
- Experiments may import `clarissa`

---

## CI Bots (for maintainers)

| Bot | What it does |
|-----|--------------|
| `gitlab_issue_bot.py` | Creates issue on CI failure |
| `gitlab_mr_bot.py` | Comments on MR when tests fail |
| `gitlab_recovery_bot.py` | Updates issue when build recovers |

Configure via CI variables: `GITLAB_TOKEN`, `CI_BOT_LABELS`, `CI_BOT_ASSIGNEE_IDS`
