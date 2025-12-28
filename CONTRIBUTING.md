# Contributing to ORSA

## ADR Discipline
If a change alters behavior, responsibilities, authority, or safety boundaries, it should:
- reference an existing ADR, or
- introduce a new ADR in `docs/adr/`.

## Boundaries
- `src/orsa/` must not import from `experiments/`.
- Experiments may import `orsa`.

## Running
```bash
python -m orsa demo
pytest -q
```


## Workflow Automation (CI Issue Bot)
CI can create or update a GitLab issue on failures. The job uses `scripts/gitlab_issue_bot.py`.
Configure via CI variables:
- `GITLAB_TOKEN` (required)
- `CI_BOT_LABELS`, `CI_BOT_ASSIGNEE_IDS` (optional)
- `CI_BOT_SILENT_MODE` (optional; "1" means comment-only)


## Merge Request Comment Bot
In MR pipelines, CI can add/update a note on the MR when tests fail via `scripts/gitlab_mr_bot.py`.


## Recovery Bot
On successful `main` push pipelines, CI can update the deduped failure issue (add a recovery note, labels, optional close)
via `scripts/gitlab_recovery_bot.py`.

## Pre-commit hooks
Install and run:
- `pip install pre-commit`
- `pre-commit install`

Hooks included:
- CLI snapshot tests
- fast unit smoke tests

To refresh snapshots: `make update-snapshots`
