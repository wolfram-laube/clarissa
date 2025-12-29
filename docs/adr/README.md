# ORSA – Architecture Decision Records (ADR Index)

## Purpose of ADRs
This directory contains Architecture Decision Records (ADRs) for ORSA.
ADRs document significant architectural decisions, their rationale, and consequences over time.

## How to Read These ADRs
- **Accepted** ADRs define the current baseline.
- **Superseded** ADRs remain for history.
- **Proposed** ADRs indicate active debate.

## ADR List
- ADR-001 — Physics-Centric, Simulator-in-the-Loop Architecture (Accepted)
- ADR-002 — Separation of Reasoning, Learning, and Governance (Accepted)
- ADR-003 — ORSA-Native Simulation Kernel (Accepted)
- ADR-004 — Dual-Simulator Strategy (Superseded)
- ADR-005 — Single-Repo Until Architecture Stabilizes (Accepted)
- ADR-006 — Noise-Free CI Artifacts and Best-Effort Jobs (Accepted)
- ADR-007 — CI as an Observability Layer (Accepted)
- ADR-008 — Governance Signals vs Enforcement (Accepted)

## Cross-References
### Architecture Diagrams
- `architecture/layered-architecture.puml`
- `architecture/learning-dialectic.puml`

### Conference
- `conference/abstract.md`

## ADR Coverage Map
| Architectural Aspect | ADR |
|---|---|
| Physics-centric learning | ADR-001 |
| Separation of roles | ADR-002 |
| Native simulation kernel | ADR-003 |
| Repo strategy | ADR-005 |
| CI hygiene & developer experience | ADR-006 |
| CI observability & reporting | ADR-007 |
| Governance signals & enforcement boundaries | ADR-008 |