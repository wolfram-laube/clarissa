# Scripts

Utility scripts for CI/CD, automation, and maintenance.

## Project Utilities

### rename_project.py

Generic parameterized script for renaming the project.

```bash
# Preview changes
python scripts/rename_project.py --dry-run

# Apply changes
python scripts/rename_project.py
```

Configure by editing `OLD_NAME` and `NEW_NAME` at the top of the script.

### update_snapshots.py

Regenerates CLI snapshots by running commands and capturing output.

```bash
python scripts/update_snapshots.py
# or
make update-snapshots
```

## CI/CD Bots

### gitlab_issue_bot.py

Creates or updates a GitLab issue when CI fails.

- Deduplicates via marker fingerprint
- Stdlib-only (no extra dependencies)
- Used by `ci_issue_on_failure` job

### gitlab_mr_bot.py

Adds or updates a Merge Request note on CI failures.

- Only runs in MR pipelines
- Summarizes test failures

### gitlab_recovery_bot.py

On successful main pipelines, updates the failure issue:

- Adds recovery note
- Updates labels
- Optionally closes issue

### gitlab_flaky_ledger_bot.py

Tracks flaky test occurrences:

- Records when rerun passes but initial failed
- Escalates after N occurrences

### ci_classify.py

Classifies failures as confirmed vs flaky:

```bash
python scripts/ci_classify.py
```

Outputs `ci_classify.env` with:

- `CI_FAILURE_TYPE` - confirmed/flaky/none
- `CI_SHOULD_NOTIFY` - true/false

## Report Generation

### generate_mr_report.py

Aggregates CI artifacts into a unified report:

```bash
python scripts/generate_mr_report.py
```

Outputs `reports/mr_report.md`.

### render_report_html.py

Converts Markdown report to HTML:

```bash
python scripts/render_report_html.py
```

Outputs `reports/mr_report.html`.

### generate_contract_summary.py

Parses contract test output and generates summary.

### detect_governance_impact.py

Heuristically detects governance-sensitive changes (e.g., RATE token modifications).

Outputs `tests/governance/impact.md`.

## Diagram Tools

### render_mermaid.sh

Renders Mermaid diagrams to SVG:

```bash
bash scripts/render_mermaid.sh
```

Requires `mermaid-cli` (mmdc).

### generate_diagram_gallery.py

Generates HTML gallery for rendered diagrams:

```bash
python scripts/generate_diagram_gallery.py
```

Outputs `docs/architecture/rendered/index.html`.

## Environment Variables

Many scripts use these CI variables:

| Variable | Purpose |
|----------|---------|
| `GITLAB_TOKEN` | API access |
| `CI_PROJECT_ID` | Project identifier |
| `CI_MERGE_REQUEST_IID` | MR number |
| `CI_PIPELINE_ID` | Pipeline identifier |
| `CI_BOT_LABELS` | Labels to apply |
| `CI_BOT_ASSIGNEE_IDS` | Assignees for issues |
| `CI_BOT_SILENT_MODE` | Suppress notifications |
