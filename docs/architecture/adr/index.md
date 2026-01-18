# CLARISSA – Architecture Decision Records (ADR Index)

## Purpose of ADRs
This directory contains Architecture Decision Records (ADRs) for CLARISSA.
ADRs document significant architectural decisions, their rationale, and consequences over time.

## How to Read These ADRs
- **Accepted** ADRs define the current baseline.
- **Proposed** ADRs indicate active design discussions.
- **Superseded** ADRs remain for historical context.

## ADR List

### Core Architecture
| ADR | Title | Status |
|-----|-------|--------|
| [001](ADR-001-physics-centric.md) | Physics-Centric, Simulator-in-the-Loop Architecture | Accepted |
| [002](ADR-002-separation-of-roles.md) | Separation of Reasoning, Learning, and Governance | Accepted |
| [003](ADR-003-native-kernel.md) | CLARISSA-Native Simulation Kernel | Accepted |
| [009](ADR-009-nlp-translation-pipeline.md) | Multi-Stage NLP Translation Pipeline | Proposed |
| [011](ADR-011-opm-flow-integration.md) | OPM Flow Integration | Accepted |

### Infrastructure & CI/CD
| ADR | Title | Status |
|-----|-------|--------|
| [006](ADR-006-noise-free-ci-artifacts.md) | Noise-free CI Artifact Directories | Accepted |
| [007](ADR-007-ci-as-observability-layer.md) | CI as an Observability Layer | Accepted |
| [012](ADR-012-container-registry-k8s-strategy.md) | Container Registry & K8s Strategy | Accepted |
| [015](ADR-015-llm-ci-notifications.md) | LLM CI Notifications | Accepted |
| [016](ADR-016-runner-load-balancing.md) | Runner Load Balancing | Accepted |
| [017](ADR-017-gdrive-folder-structure.md) | GDrive Folder Structure | Accepted |

### Repository & Process
| ADR | Title | Status |
|-----|-------|--------|
| [005](ADR-005-repo-decomposition.md) | Single Repository Until Architecture Stabilizes | Accepted |
| [008](ADR-008-governance-signals-vs-enforcement.md) | Governance Signals vs Enforcement | Accepted |
| [010](ADR-010-project-renaming-clarissa.md) | Project Renaming to CLARISSA | Accepted |
| [013](ADR-013-i18n-architecture.md) | Internationalization Architecture | Accepted |
| [014](ADR-014-llm-document-merge.md) | LLM Document Merge | Accepted |
| [018](ADR-018-gitlab-pm-workflow.md) | GitLab-Native Project Management Workflow | Accepted |

### Superseded
| ADR | Title | Status | Superseded By |
|-----|-------|--------|---------------|
| [004](ADR-004-dual-simulator-strategy.md) | Dual-Simulator Strategy | Superseded | ADR-001 |

## ADR Coverage Map

| Architectural Aspect | ADR |
|----------------------|-----|
| Physics-centric learning | ADR-001 |
| Separation of roles (LLM/RL/Governance) | ADR-002 |
| Native simulation kernel | ADR-003 |
| NLP translation pipeline | ADR-009 |
| OPM Flow integration | ADR-011 |
| Repository strategy | ADR-005 |
| CI hygiene & developer experience | ADR-006 |
| CI observability & reporting | ADR-007 |
| Governance signals & enforcement | ADR-008 |
| Container & K8s strategy | ADR-012 |
| Internationalization | ADR-013 |
| LLM document processing | ADR-014 |
| CI notifications | ADR-015 |
| Runner load balancing | ADR-016 |
| GDrive organization | ADR-017 |
| Development workflow | ADR-018 |

## Cross-References

### Architecture Diagrams
- `docs/architecture/diagrams/*.mmd` — Mermaid sources
- `architecture/layered-architecture.puml` — PlantUML overview
- `architecture/learning-dialectic.puml` — Learning flow

### Conference Artifacts
- `conference/abstract.md` — CLARISSA abstract
- `conference/ijacsa-2026/` — IJACSA 2026 paper submission

### Implementation
- `src/clarissa/agent/` — Agent core (ADR-002)
- `src/clarissa/governance/` — Governance policy (ADR-002, ADR-008)
- `src/clarissa_kernel/` — Native kernel (ADR-003)
- `docs/simulators/adapter_matrix.md` — Simulator backends (ADR-001)

## Creating New ADRs

Use the template: [ADR-000-template.md](ADR-000-template.md)

**Naming convention:** `ADR-NNN-short-descriptive-title.md`

**When to create an ADR:**
- Introducing a new architectural component
- Changing responsibilities or boundaries
- Making technology choices with long-term impact
- Establishing patterns or conventions
