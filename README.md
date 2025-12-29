# CLARISSA – Conversational Language Agent for Reservoir Integrated Simulation System Analysis

**A physics-centric AI agent architecture for reservoir simulation.**

CLARISSA bridges natural language interaction and domain-specific simulation syntax through governed, simulator-in-the-loop learning.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run demo (interactive approval)
python -m clarissa demo

# Run demo (CI mode, auto-approve)
AUTO_APPROVE=1 python -m clarissa demo

# Run tests
pytest -q
```

## Repository Structure

```
src/clarissa/           # Importable CLARISSA package
  ├── agent/        # Agent core (reasoning, planning)
  ├── governance/   # Policy enforcement, approval gates
  ├── learning/     # RL components (planned)
  └── simulators/   # Simulator adapters

src/clarissa_kernel/    # Native simulation kernel (laboratory)

docs/
  ├── adr/          # Architecture Decision Records
  ├── architecture/ # Diagrams (Mermaid)
  └── simulators/   # Adapter specifications

conference/         # Academic artifacts (abstracts, papers)
experiments/        # Exploratory work (may import clarissa)
scripts/            # CI/CD tooling, bots
tests/              # Contract tests, golden tests, snapshots
```

## Core Principles

> **Learning flows from numerical consequences.**  
> **Authority flows from human approval.**

1. **Physics-Centric** (ADR-001): Simulators are first-class learning substrates. Numerical outcomes—not text plausibility—drive feedback.

2. **Separation of Roles** (ADR-002): LLM reasoning, RL learning, and governance are architecturally separate for auditability.

3. **Signals over Enforcement** (ADR-008): CI detects and reports governance-relevant changes; humans decide and act.

## Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| [001](docs/adr/ADR-001-physics-centric.md) | Physics-Centric, Simulator-in-the-Loop | Accepted |
| [002](docs/adr/ADR-002-separation-of-roles.md) | Separation of Reasoning, Learning, Governance | Accepted |
| [003](docs/adr/ADR-003-native-kernel.md) | CLARISSA-Native Simulation Kernel | Accepted |
| [005](docs/adr/ADR-005-repo-decomposition.md) | Single Repo Until Stabilization | Accepted |
| [006](docs/adr/ADR-006-noise-free-ci-artifacts.md) | Noise-free CI Artifacts | Accepted |
| [007](docs/adr/ADR-007-ci-as-observability-layer.md) | CI as Observability Layer | Accepted |
| [008](docs/adr/ADR-008-governance-signals-vs-enforcement.md) | Governance Signals vs Enforcement | Accepted |
| [009](docs/adr/ADR-009-nlp-translation-pipeline.md) | Multi-Stage NLP Translation Pipeline | Proposed |

## Testing

```bash
# All tests
make test

# Contract tests (simulator adapter invariants)
pytest tests/contracts/ -v

# Snapshot tests (CLI stability)
pytest tests/golden/ -v

# Update snapshots after intentional CLI changes
make update-snapshots
```

## CI/CD

The CI pipeline implements an **observability model** (ADR-007):

- **Test Stage:** Collect evidence (JUnit, snapshots, contracts)
- **Classify Stage:** Determine verdict (confirmed failure vs flaky)
- **Automation Stage:** Generate reports, notify via bots

Governance-sensitive changes are **detected and reported**, not automatically blocked (ADR-008).

## Development

```bash
# Install with dev dependencies
make dev

# Run linter
ruff check src/ tests/

# Generate MR report locally
make mr-report
make mr-report-html
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Simulator Adapters

See [docs/simulators/adapter_matrix.md](docs/simulators/adapter_matrix.md).

| Backend | Status | Notes |
|---------|--------|-------|
| MockSimulator | ✅ Implemented | CI-friendly, deterministic |
| OPM Flow | 🟡 Planned | Open-source, ECLIPSE-compatible |
| MRST | 🟡 Planned | MATLAB-based, research-friendly |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

**Key rule:** If a change affects behavior, responsibilities, or safety boundaries, it should reference or introduce an ADR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

Proprietary – Oxy / BlauWeiss LLC
