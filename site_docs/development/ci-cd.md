# CI/CD Pipeline

CLARISSA uses GitLab CI with an **observability-focused model** (see [ADR-007](../architecture/adr/ADR-007-ci-as-observability-layer.md)).

## Philosophy

CI primarily functions as a **source of diagnostic signals**, not solely as a merge gate.

!!! info "Key Principle"
    Generate evidence → Interpret evidence → Publish evidence

## Pipeline Stages

### 1. Test Stage

Collects evidence:

| Job | Purpose | Artifacts |
|-----|---------|-----------|
| `tests` | Unit & integration tests | JUnit XML |
| `contract_tests` | Simulator adapter invariants | Summary |
| `snapshot_tests` | CLI output stability | Diffs |
| `governance_impact` | Detect sensitive changes | Impact report |
| `architecture_graphs` | Render Mermaid diagrams | SVGs |

### 2. Classify Stage

| Job | Purpose |
|-----|---------|
| `ci_classify` | Determine verdict (confirmed vs flaky) |

Outputs `ci_classify.env` with machine-readable classification.

### 3. Automation Stage

| Job | Trigger | Action |
|-----|---------|--------|
| `mr_report` | MR pipeline | Generate report |
| `mr_comment_on_failure` | MR + failure | Comment on MR |
| `ci_issue_on_failure` | main + failure | Create/update issue |
| `ci_issue_on_recovery` | main + success | Add recovery note |
| `ci_flaky_ledger` | main + flaky | Track flaky tests |
| `pages` | main push | Deploy docs site |

## Governance Signals

Per [ADR-008](../architecture/adr/ADR-008-governance-signals-vs-enforcement.md):

- CI **detects** governance-relevant changes
- CI **reports** them prominently
- CI does **not block** automatically
- **Humans decide** and act

## Running Locally

```bash
# Run all tests
make test

# Generate MR report
make mr-report
make mr-report-html

# Update snapshots
make update-snapshots
```

## Artifacts

On MR pipelines, find in job artifacts:

- `reports/mr_report.md` - Markdown summary
- `reports/mr_report.html` - HTML version
- `tests/golden/summary.md` - Snapshot diffs (on failure)
- `tests/contracts/summary.md` - Contract failures (on failure)
- `tests/governance/impact.md` - Governance signals

## Flaky Test Handling

1. Initial failure triggers `tests_rerun`
2. If rerun passes → classified as **flaky**
3. Flaky events tracked in ledger
4. After N occurrences → escalation issue created

This separates deterministic failures from environmental issues.
