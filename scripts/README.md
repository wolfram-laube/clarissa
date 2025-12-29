# Scripts

## rename_project.py
Generic parameterized script for renaming the project across all files and directories.

**Configuration:** Edit `OLD_NAME` and `NEW_NAME` dictionaries at the top of the script.

**Usage:**
```bash
# Preview changes (no modifications)
python scripts/rename_project.py --dry-run

# Apply changes
python scripts/rename_project.py
```

**Features:**
- Renames packages (`src/clarissa/` → `src/newname/`)
- Updates all text content (imports, references, documentation)
- Renames binary files (PDFs, PNGs, etc.)
- Handles compound terms (CLARISSAAgent, clarissa_kernel, etc.)
- Batched commits for large changesets

**Note:** After renaming, update CLI snapshots in `tests/golden/snapshots/` to match new output.

---

## CI/CD Bots

### gitlab_issue_bot.py
Creates or updates a GitLab issue when CI fails, with dedupe via a marker fingerprint.
Stdlib-only: no extra Python deps.

Used by `.gitlab-ci.yml` in the `ci_issue_on_failure` job.

### gitlab_mr_bot.py
Adds or updates a GitLab Merge Request note on CI failures in MR pipelines.

### gitlab_recovery_bot.py
On successful main pipelines, updates the deduped CI failure issue (note + labels, optional close).

### ci_classify.py
Classifies failures as confirmed vs flaky using a single rerun; emits dotenv vars.

### gitlab_flaky_ledger_bot.py
Records flaky events on main (rerun passed) and escalates after N occurrences.

### gitlab_mr_snapshot_bot.py
Posts snapshot diff summary.md to MR as a deduped note on snapshot failure.

---

## Report Generation

### generate_contract_summary.py
Parses contract test output log and writes tests/contracts/summary.md for MR reporting.

### detect_governance_impact.py
Heuristically detects governance-sensitive changes (RATE token) in MR diffs and writes tests/governance/impact.md.

### generate_mr_report.py
Generates reports/mr_report.md from CI summaries and env vars.

### render_report_html.py
Renders reports/mr_report.md to reports/mr_report.html (minimal HTML renderer).

---

## Utilities

### update_snapshots.py
Regenerates CLI snapshots by running commands and capturing output.

### render_mermaid.sh
Renders Mermaid diagrams to SVG (requires mermaid-cli).

### generate_diagram_gallery.py
Generates an HTML gallery index for rendered architecture diagrams.
