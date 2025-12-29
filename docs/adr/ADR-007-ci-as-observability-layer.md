# ADR-007: CI as an Observability Layer (Classification, Reporting, and Bots)

## Status
Accepted

## Context
ORSA development relies on iterative changes across code, docs, and governance-related logic.
Traditional CI setups tend to act as a hard gate: either "green" or "red".
This becomes counterproductive when:
- failures can be flaky or environment-dependent,
- we want fast feedback loops without blocking work,
- we need structured, explainable signals rather than raw logs,
- governance-relevant changes need visibility, not necessarily blanket blocking.

We already maintain:
- unit/integration tests (`tests`)
- golden/snapshot tests (`snapshot_tests`)
- contract tests (`contract_tests`)
- governance impact detection (`governance_impact`)
- optional diagram rendering (`architecture_graphs`)
- a rerun job to detect flakiness (`tests_rerun`)
- a classifier that emits a machine-readable verdict (`ci_classify.env`)
- MR report generation and optional MR comments/bots.

The design intent is to treat CI as a source of *diagnostic signals* (observability),
not solely as a merge gate.

## Decision
We adopt a layered CI model where CI primarily functions as an observability layer:

1. **Signal collection (test stage)**
   - Jobs produce evidence: JUnit XML, summaries, rendered diagrams, governance notes.
   - Optional jobs may fail without blocking the overall pipeline (e.g. rendering).

2. **Signal refinement (rerun stage)**
   - When a failure occurs, a targeted rerun may be executed to separate:
     - deterministic failures from flaky failures.

3. **Signal classification (classify stage)**
   - A dedicated classification job computes a compact verdict and exports it as dotenv:
     `ci_classify.env`.
   - The classifier is the single source of truth for high-level CI interpretation.

4. **Signal publishing (automation stage)**
   - MR report generation aggregates artifacts into a human-readable summary.
   - Bots MAY create issues or MR comments, but MUST be best-effort and non-blocking.

This establishes a clear separation between:
- generating evidence,
- interpreting evidence,
- publishing evidence.

## Consequences

### Positive
- Developers receive actionable, structured feedback (not just raw logs).
- Flaky behavior can be identified explicitly and tracked over time.
- Governance-related changes become visible and auditable in the MR lifecycle.
- Optional tooling (diagram rendering) improves quality without increasing fragility.
- Clear responsibilities align with ADR-002 (separation of roles).

### Negative
- Slightly more CI complexity (more jobs, artifacts, and scripts).
- Requires discipline to keep classifier outputs stable and meaningful.
- Some failures may not block merges automatically; teams must respect the signals.

## Implementation Notes
- The classifier MUST produce a minimal stable contract (dotenv keys) consumed by reports/bots.
- Bots MUST never fail the pipeline; they should log errors and exit 0.
- Artifact paths should be created at runtime to avoid CI noise (see ADR-006).
- Governance detection should be visible (reporting) and may later evolve into
  enforceable policies (manual approval steps) if required.

## Cross-References
- ADR-002 — Separation of Reasoning, Learning, and Governance
- ADR-006 — Noise-free CI artifact directories
- `scripts/ci_classify.py`
- `scripts/generate_mr_report.py`
- `.gitlab-ci.yml`
