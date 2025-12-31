# Changelog

All notable changes to the CLARISSA project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ADR-009: Multi-Stage NLP Translation Pipeline (Proposed)
- IJACSA 2026 paper draft with architecture diagrams (`conference/ijacsa-2026/`)

### Changed
- Extracted version history from README into CHANGELOG.md

---

## [0.3.0] - 2025-12-28

### Added
- **Snapshot Testing System (v24-v30)**
  - Snapshot-style CLI tests in `tests/golden/snapshots/`
  - `make update-snapshots` for regenerating baselines
  - CI job `snapshot_tests` with diff artifact uploads
  - Summary generation for MR reports

- **Architecture Diagram Gallery (v23-v24)**
  - Mermaid diagrams in `docs/architecture/diagrams/`
  - CI rendering to SVG (best-effort)
  - Gallery index generation

- **Simulator Adapter Matrix (v23)**
  - `docs/simulators/adapter_matrix.md` documenting backend contracts
  - MockSimulator as reference implementation
  - MRST and OPM Flow planned

- **MR Reporting System (v20-v22)**
  - Unified MR report aggregating snapshots, contracts, governance signals
  - HTML export via `make mr-report-html`
  - CI artifact generation in `reports/`

- **Governance Impact Detection (v19)**
  - Heuristic detection of governance-sensitive changes
  - `scripts/detect_governance_impact.py`
  - Integration into MR reports

- **Contract Test Framework (v18)**
  - `tests/contracts/` enforcing simulator adapter invariants
  - Summary generation for CI artifacts

### Changed
- CI observability model formalized in ADR-007
- Governance signals vs enforcement clarified in ADR-008

---

## [0.2.0] - 2025-12-27

### Added
- **CI Classification System (v10-v17)**
  - `ci_classify.py` emitting machine-readable verdicts
  - Flaky vs confirmed failure detection via rerun
  - `ci_classify.env` dotenv output

- **GitLab Bot Infrastructure (v9-v16)**
  - `gitlab_issue_bot.py` - Issue creation/update on failures
  - `gitlab_mr_bot.py` - MR comment on failures
  - `gitlab_recovery_bot.py` - Recovery notes on green main
  - `gitlab_flaky_ledger_bot.py` - Flaky test tracking
  - Deduplication via fingerprint markers
  - Label taxonomy (confirmed vs flaky)

- **Rerun Infrastructure (v10-v11)**
  - `tests_rerun` job using pytest `--last-failed`
  - Early termination with `--maxfail` and `-x`

- **ADRs 005-008**
  - ADR-005: Single Repository Until Architecture Stabilizes
  - ADR-006: Noise-free CI Artifact Directories
  - ADR-007: CI as an Observability Layer
  - ADR-008: Governance Signals vs Enforcement

### Changed
- CI pipeline restructured into stages: test → classify → automation
- Artifact handling improved to reduce CI log noise

---

## [0.1.0] - 2025-12-26

### Added
- **Core Agent Architecture**
  - `src/clarissa/agent/core.py` - CLARISSAAgent with governance gate
  - `src/clarissa/governance/policy.py` - GovernancePolicy with approval logic
  - `src/clarissa/simulators/mock.py` - MockSimulator for testing
  - `src/clarissa_kernel/core.py` - NativeKernel for explainability

- **CLI**
  - `python -m clarissa demo` - Interactive governed demo
  - `python -m clarissa --help` - Help output
  - `AUTO_APPROVE=1` for CI-friendly execution

- **Foundational ADRs**
  - ADR-001: Physics-Centric, Simulator-in-the-Loop Architecture
  - ADR-002: Separation of Reasoning, Learning, and Governance
  - ADR-003: CLARISSA-Native Simulation Kernel
  - ADR-004: Dual-Simulator Strategy (Superseded)

- **Project Infrastructure**
  - `pyproject.toml` with modern Python packaging
  - `Makefile` with standard targets
  - `.gitlab-ci.yml` with test pipeline
  - `CONTRIBUTING.md` with ADR discipline guidelines

- **Conference Artifacts**
  - `conference/abstract.md` - CLARISSA abstract

---

## Version Naming Note

Internal development versions (v1-v30) tracked incremental CI and tooling improvements.
These have been consolidated into semantic versions for external clarity.

| Semantic Version | Internal Versions | Focus |
|------------------|-------------------|-------|
| 0.1.0 | v1-v8 | Core architecture, ADRs 001-004 |
| 0.2.0 | v9-v17 | CI bots, classification, ADRs 005-008 |
| 0.3.0 | v18-v30 | Contracts, snapshots, MR reports, diagrams |
