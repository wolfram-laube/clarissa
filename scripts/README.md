# Scripts

## gitlab_issue_bot.py
Creates or updates a GitLab issue when CI fails, with dedupe via a marker fingerprint.
Stdlib-only: no extra Python deps.

Used by `.gitlab-ci.yml` in the `ci_issue_on_failure` job.

## gitlab_mr_bot.py
Adds or updates a GitLab Merge Request note on CI failures in MR pipelines.

## gitlab_recovery_bot.py
On successful main pipelines, updates the deduped CI failure issue (note + labels, optional close).

## ci_classify.py
Classifies failures as confirmed vs flaky using a single rerun; emits dotenv vars.

## gitlab_flaky_ledger_bot.py
Records flaky events on main (rerun passed) and escalates after N occurrences.


### Label taxonomy
v9 standardizes labels across MR notes and Issues (confirmed vs flaky).


### v10
CI rerun re-executes only failing tests using pytest's --last-failed cache.


### v11
Rerun stops early using --maxfail and -x to reduce confirmation cost.

## gitlab_mr_snapshot_bot.py
Posts snapshot diff summary.md to MR as a deduped note on snapshot failure.

## generate_contract_summary.py
Parses contract test output log and writes tests/contracts/summary.md for MR reporting.

## detect_governance_impact.py
Heuristically detects governance-sensitive changes (RATE token) in MR diffs and writes tests/governance/impact.md.

## generate_mr_report.py
Generates reports/mr_report.md from CI summaries and env vars.

## render_report_html.py
Renders reports/mr_report.md to reports/mr_report.html (minimal HTML renderer).
