# Architecture Decision Records

Architecture Decision Records (ADRs) document significant architectural decisions, their rationale, and consequences.

## How to Read ADRs

| Status | Meaning |
|--------|---------|
| **Accepted** | Current baseline, actively followed |
| **Proposed** | Under discussion, not yet finalized |
| **Superseded** | Replaced by another ADR, kept for history |

## ADR Index

### Core Architecture

| ADR | Title | Status |
|-----|-------|--------|
| [001](ADR-001-physics-centric.md) | Physics-Centric, Simulator-in-the-Loop | Accepted |
| [002](ADR-002-separation-of-roles.md) | Separation of Reasoning, Learning, Governance | Accepted |
| [003](ADR-003-native-kernel.md) | CLARISSA-Native Simulation Kernel | Accepted |
| [009](ADR-009-nlp-translation-pipeline.md) | Multi-Stage NLP Translation Pipeline | Proposed |

### Repository & Process

| ADR | Title | Status |
|-----|-------|--------|
| [005](ADR-005-repo-decomposition.md) | Single Repository Until Stabilization | Accepted |
| [006](ADR-006-noise-free-ci-artifacts.md) | Noise-free CI Artifact Directories | Accepted |
| [007](ADR-007-ci-as-observability-layer.md) | CI as an Observability Layer | Accepted |
| [008](ADR-008-governance-signals-vs-enforcement.md) | Governance Signals vs Enforcement | Accepted |

### Superseded

| ADR | Title | Superseded By |
|-----|-------|---------------|
| [004](ADR-004-dual-simulator-strategy.md) | Dual-Simulator Strategy | ADR-001 |

## Coverage Map

| Aspect | ADR |
|--------|-----|
| Physics-centric learning | ADR-001 |
| Separation of roles | ADR-002 |
| Native simulation kernel | ADR-003 |
| NLP translation pipeline | ADR-009 |
| Repository strategy | ADR-005 |
| CI hygiene | ADR-006 |
| CI observability | ADR-007 |
| Governance boundaries | ADR-008 |

## Creating New ADRs

1. Copy `ADR-000-template.md`
2. Use next available number
3. Follow naming: `ADR-NNN-short-title.md`
4. Submit via Merge Request

**When to create an ADR:**

- Introducing new architectural components
- Changing responsibilities or boundaries  
- Making technology choices with long-term impact
- Establishing patterns or conventions
