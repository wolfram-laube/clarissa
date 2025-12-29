# ORSA – Unified Code & Documentation Repository

This repository contains the ORSA (Oxy Reservoir Simulation Agent) codebase **and** its governing documentation.
Architecture decisions live in `docs/adr/` and are first-class citizens.

## Structure (high level)
- `src/orsa/` – importable ORSA package (agent, governance, learning, simulator adapters, CLI)
- `src/orsa_kernel/` – lightweight native simulation kernel package (laboratory, explainability, learning signals)
- `docs/adr/` – Architecture Decision Records (ADRs)
- `architecture/` – diagrams (PUML/SVG) and architecture visuals
- `conference/` – conference artifacts (abstract, keywords, etc.)
- `experiments/` – exploratory work (may import `orsa`, never the reverse)
- `scripts/` – operational tooling

## Quick start
```bash
python -m orsa --help
python -m orsa demo
pytest -q
```

## Control principle
Learning flows from numerical consequences.
Authority flows from human approval.


## CI-friendly demo
Set `ORSA_AUTO_APPROVE=1` to run the demo without interactive approval.

## CI philosophy (important)
ORSA CI is designed as an observability and reporting system, not a strict
pass/fail gate.

A green pipeline indicates a healthy system state.
A red pipeline indicates a signal that requires inspection, not automatic rejection.

Always consult the MR report for context, including:
- snapshot (golden) diffs
- contract test outcomes
- governance-impact heuristics

Details: docs/ci/README.md


## Tests
- Contract tests: `tests/contracts/` enforce simulator adapter invariants.
- Golden CLI tests: `tests/golden/` ensure stable CLI UX.
- Update golden markers: `make update-golden`.

### CLI snapshots
Snapshot-style tests live in `tests/golden/snapshots/`.
Update them with:
- `make update-snapshots`

## Dev hygiene
Optional: enable pre-commit hooks to keep CLI snapshots and fast tests green.
- `pip install pre-commit`
- `pre-commit install`

### Snapshot debug artifacts (CI)
If CLI snapshots mismatch, the test suite writes:
- `tests/golden/diffs/` (diffs)
- `tests/golden/actuals/` (actual normalized output)
CI uploads them from the `snapshot_tests` job.

### v17: CI diff summary
On snapshot failures, CI creates `tests/golden/summary.md` containing embedded diffs and uploads it as an artifact.

## v20: Unified MR report
MR comments now embed snapshot diffs, contract failures, and a governance-impact heuristic section.

## v21: Review ergonomics
Merge Requests now show a status table (snapshots, contracts, governance) and direct CI links.

## v22: Exportable MR reports
Generate report artifacts locally:
- `make mr-report`
- `make mr-report-html`
CI creates artifacts on MR pipelines in `reports/`.

## v23: Casino Royale (diagrams + adapter matrix)
- Simulator adapter matrix: `docs/simulators/adapter_matrix.md`
- Mermaid architecture diagrams: `docs/architecture/diagrams/`
- CI attempts to render SVGs: `docs/architecture/rendered/` (best-effort)

## v24: Diagram gallery
CI renders Mermaid diagrams and generates a gallery at `docs/architecture/rendered/index.html` (see artifacts).
