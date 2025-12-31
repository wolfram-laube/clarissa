# ADR-005: Single Repository Until Architecture Stabilizes

**Status:** Accepted  
**Date:** 2025-12-27

## Context
CLARISSA is currently co-evolving across architecture (ADRs/diagrams), prototype code, and conference artifacts. Splitting repositories too early increases drift, reduces traceability, and weakens governance discipline.

## Decision
Maintain a single repository that contains:
- the importable CLARISSA package (`src/clarissa/`),
- the CLARISSA-native kernel package (`src/clarissa_kernel/`),
- governing documentation (`docs/adr/`, `architecture/`),
- conference artifacts (`conference/`),
- experiments (`experiments/`) and tooling (`scripts/`).

Repository decomposition will be revisited only when the architecture stabilizes (ADR churn slows), the prototype becomes reusable by others, and independent release cadence is required.

## Consequences
### Positive
- Strong traceability between ADRs and code.
- Simplifies onboarding and review.
### Negative
- Requires clear internal boundaries (no `clarissa` importing `experiments`).
### Neutral / Open
- Future split may create `clarissa-architecture`, `clarissa-core`, and `clarissa-experiments` repositories.
