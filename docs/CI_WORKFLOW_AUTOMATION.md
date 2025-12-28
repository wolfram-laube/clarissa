# CI Workflow Automation (v7: confirm-then-escalate)

Channels:
1. **Main branch pushes:** create/update a deduped Issue for **confirmed** failures.
2. **Merge request pipelines:** add/update a MR note for failures; if rerun passes, mark as **flaky-suspected**.

## Confirm-Then-Escalate
A failing test run triggers a single rerun (`tests_rerun`) on MR pipelines and on `main` pushes.
Classification writes dotenv variables:
- `CI_BOT_CONFIRMED_FAILURE=1` when rerun also fails (or rerun not available)
- `CI_BOT_FLAKY=1` when first run fails but rerun passes

Automation jobs consume these variables and gate issue creation accordingly.

## Required CI Variable
- `GITLAB_TOKEN`

## Optional variables
Issue bot:
- `CI_BOT_LABELS`, `CI_BOT_ASSIGNEE_IDS`, `CI_BOT_ASSIGNEE_ROTATION_IDS`
- `CI_BOT_CREATE_AFTER_N_FAILURES` (still supported; applies after confirmation gating)
Recovery bot:
- `CI_BOT_RECOVERY_LABELS`, `CI_BOT_MARK_FLAKY_ON_RECOVERY`, `CI_BOT_CLOSE_ON_RECOVERY`
MR bot:
- none required; it uses classification vars to phrase the note


## Flaky ledger + escalation (v8)
On `main` pushes where the first test run fails but the rerun passes (`CI_BOT_FLAKY=1`), CI records the event in a
single ledger issue and escalates to a dedicated "flaky suspected" issue after N occurrences.

Variables:
- `CI_BOT_FLAKY_ESCALATE_AFTER_N` (default 3)
- `CI_BOT_FLAKY_ESCALATION_LABELS` (default `ci,ci-flaky-suspected`)

## MR labeling (v8)
If an MR run is classified as flaky, the MR bot can apply a label to the MR:
- `CI_BOT_MR_FLAKY_LABEL` (default `ci-flaky-suspected`)


## Label taxonomy (v9)
To keep the signal consistent across Issues and Merge Requests, v9 standardizes labels:

- Confirmed regression: `ci-regression-confirmed`
- Flaky suspected: `ci-flaky-suspected`
- Generic CI failure: `ci-failure`
- Recovered: `recovered` (or `ci,recovered` depending on your label scheme)

Merge Request label env vars:
- `CI_BOT_MR_CONFIRMED_LABEL` (default `ci-regression-confirmed`)
- `CI_BOT_MR_FLAKY_LABEL` (default `ci-flaky-suspected`)

Issue bot labels:
- `CI_BOT_LABELS` default now includes `ci-regression-confirmed` when confirmed.


## v10: Fast rerun (only failing tests)
`tests_rerun` now re-runs only the tests that failed in the first run using pytest's cache:

- First run stores `.pytest_cache/` as an artifact.
- Rerun uses:
  - `pytest --last-failed --last-failed-no-failures=none`

This makes confirm-then-escalate much faster on large test suites.


## v11: Fast rerun with early exit
`tests_rerun` still uses `--last-failed`, but now exits early to save time when failures are persistent:

- `--maxfail=${CI_BOT_RERUN_MAXFAIL:-1}`
- `-x` (stop after first failure)

Optional CI variable:
- `CI_BOT_RERUN_MAXFAIL` (default `1`) — increase if you want broader reconfirmation.


## v14: Snapshot-based CLI golden tests
Golden CLI tests now use normalized snapshots with readable diffs. Update via `make update-snapshots`.


## v15: Dedicated snapshot/contract CI jobs
CI now runs `snapshot_tests` and `contract_tests` as explicit jobs for clearer feedback.


## v16: Snapshot diff artifacts
On snapshot mismatches, tests write artifacts:
- `tests/golden/diffs/*.diff` (unified diff)
- `tests/golden/actuals/*` (normalized actual output)
`snapshot_tests` uploads these as CI artifacts for easy debugging.


## v17: Snapshot artifacts only on failure + summary
`snapshot_tests` now uploads snapshot artifacts only when tests fail (saves storage) and generates `tests/golden/summary.md` with embedded diffs.


## v18: MR snapshot diff notes
On MR pipelines, snapshot failures now post `tests/golden/summary.md` to the MR as a deduped note via `scripts/gitlab_mr_snapshot_bot.py`.


## v19: Unified MR note
Snapshot diff summaries are now embedded into the main MR note produced by `scripts/gitlab_mr_bot.py` (single deduped note), removing the separate snapshot-note bot.


## v20: MR report includes contracts + governance
MR note now embeds:
- Snapshot summary (`tests/golden/summary.md`)
- Contract summary (`tests/contracts/summary.md`) generated from contract_tests output
- Governance impact heuristic (`tests/governance/impact.md`) generated from MR changes

New scripts:
- `scripts/generate_contract_summary.py`
- `scripts/detect_governance_impact.py`


## v21: MR status table and links
Unified MR note now starts with a compact CI status table and ends with pipeline/job links.


## v22: Exportable MR report artifacts
On MR pipelines, CI generates `reports/mr_report.md` (and a minimal `reports/mr_report.html`) as artifacts via the `mr_report` job.
Commands:
- `make mr-report`
- `make mr-report-html`


## v23: Architecture diagrams + simulator adapter matrix
- Added `docs/simulators/adapter_matrix.md`.
- Added Mermaid diagrams in `docs/architecture/diagrams/`.
- CI job `architecture_graphs` (best-effort, allow_failure) renders SVGs into `docs/architecture/rendered/` and uploads artifacts.


## v24: Diagram gallery + reliable rendering image
- `architecture_graphs` now uses the official mermaid-cli container image for more reliable headless rendering.
- After rendering, CI generates `docs/architecture/rendered/index.html` and `index.md` as a gallery index.
