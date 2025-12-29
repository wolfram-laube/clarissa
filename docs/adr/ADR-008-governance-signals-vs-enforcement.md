# ADR-008: Governance Signals vs Enforcement

## Status
Accepted

## Context
ORSA operates in a domain where changes may have:
- physical implications (simulation parameters, rates, constraints),
- governance implications (compliance, approvals, auditability),
- research implications (exploration, experimentation, iteration).

In such environments, governance mechanisms are often implemented as
hard enforcement rules inside CI/CD pipelines, e.g.:
- blocking merges on heuristic matches,
- mandatory approvals triggered automatically,
- policy-as-code gates with binary outcomes.

This approach creates several problems for ORSA:
- governance logic becomes opaque and brittle,
- false positives lead to unnecessary friction,
- experimentation is discouraged,
- responsibility is shifted from humans to automation.

At the same time, *ignoring governance signals entirely* is not acceptable,
as traceability, visibility, and accountability are required.

## Decision
ORSA explicitly distinguishes between **governance signals** and **governance enforcement**.

### Governance Signals
Governance signals are:
- heuristic or rule-based detections,
- informational in nature,
- produced automatically,
- visible in CI artifacts and MR reports,
- intended to **inform human decision-making**.

Examples:
- detection of changes to rate parameters (`RATE` tokens),
- changes in governed configuration sections,
- deviations from expected simulation behavior,
- classified CI outcomes (e.g. "potentially flaky", "needs review").

Governance signals MUST:
- be surfaced clearly and consistently,
- never block the pipeline by themselves,
- be explainable and auditable.

### Governance Enforcement
Governance enforcement is:
- a **human decision**,
- contextual and situational,
- potentially involving approvals, sign-offs, or process steps.

Enforcement MAY be implemented via:
- manual approval steps,
- documented review procedures,
- external governance workflows.

Enforcement MUST NOT be:
- implicit,
- fully automated based on heuristics alone,
- hidden inside CI failure conditions.

## Consequences

### Positive
- Clear separation of automation and responsibility.
- Reduced false positives and CI friction.
- Governance logic remains transparent and reviewable.
- Experimentation and research workflows remain viable.
- CI outputs become trustworthy signals rather than threats.

### Negative
- Requires human discipline to act on signals.
- Reviewers must actively read and interpret reports.
- Fewer automatic “hard stops” than traditional CI setups.

These trade-offs are **explicitly accepted** in favor of correctness,
explainability, and long-term system integrity.

## Rationale
Governance is inherently normative and contextual.
Automated systems can detect patterns, but they cannot:
- fully assess intent,
- understand situational risk,
- balance competing objectives.

ORSA therefore treats governance automation as:
- **sensing**, not judging,
- **highlighting**, not enforcing,
- **supporting**, not replacing human oversight.

This aligns with:
- ADR-002 (Separation of Reasoning, Learning, and Governance),
- ADR-007 (CI as an Observability Layer).

## Implementation Notes
- CI jobs performing governance detection MUST be best-effort and non-blocking.
- Governance findings SHOULD be written to explicit artifacts (e.g. `impact.md`).
- MR reports SHOULD aggregate governance signals prominently.
- Any future enforcement mechanisms MUST be explicit and human-triggered.

## Cross-References
- ADR-002 — Separation of Reasoning, Learning, and Governance
- ADR-006 — Noise-free CI artifact directories
- ADR-007 — CI as an Observability Layer
- `scripts/detect_governance_impact.py`
- `scripts/generate_mr_report.py`
