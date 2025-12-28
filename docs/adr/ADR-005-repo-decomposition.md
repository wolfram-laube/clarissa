# ADR-005: Single Repository Until Architecture Stabilizes

**Status:** Accepted  
**Date:** 2025-12-27

## Context
ORSA is currently co-evolving across architecture (ADRs/diagrams), prototype code, and conference artifacts. Splitting repositories too early increases drift, reduces traceability, and weakens governance discipline.

## Decision
Maintain a single repository that contains:
- the importable ORSA package (`src/orsa/`),
- the ORSA-native kernel package (`src/orsa_kernel/`),
- governing documentation (`docs/adr/`, `architecture/`),
- conference artifacts (`conference/`),
- experiments (`experiments/`) and tooling (`scripts/`).

Repository decomposition will be revisited only when the architecture stabilizes (ADR churn slows), the prototype becomes reusable by others, and independent release cadence is required.

## Consequences
### Positive
- Strong traceability between ADRs and code.
- Simplifies onboarding and review.
### Negative
- Requires clear internal boundaries (no `orsa` importing `experiments`).
### Neutral / Open
- Future split may create `orsa-architecture`, `orsa-core`, and `orsa-experiments` repositories.
