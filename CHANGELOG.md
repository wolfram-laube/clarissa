# Changelog

All notable changes to the CLARISSA project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Voice Roundtrip Notebook (17)** (2026-01-26)
  - Cross-platform voice input testing notebook for local machines
  - Audio recording via `sounddevice` (Mac/Windows/Linux)
  - Whisper API transcription with reservoir domain vocabulary
  - Rule-based + LLM intent parsing (Claude/GPT-4 fallback)
  - 10 test utterances for validation
  - Ref: ADR-028

- **GitLab Runner Infrastructure: 12/12 Runners Operational** (2026-01-17)
  - K3s Kubernetes cluster on GCP VM configured for GitLab Runner
  - New `.gitlab/k3s-setup.yml` with installation and management jobs
  - All 12 runners now functional: 4 machines × 3 executors (shell, docker, k8s)
  - Machines: Mac #1, Mac #2, Linux Yoga, GCP VM

- **Automated Benchmark Report Generation** (2026-01-17)
  - New `benchmark-report` job in `.gitlab/benchmark.yml`
  - Generates 4 PNG charts: by_machine, by_executor, detailed, heatmap
  - Uses matplotlib for visualization
  - Collects timing data from all 12 benchmark jobs via GitLab API

- **LLM-Powered Email Generation** (2026-01-17)
  - New `scripts/ci/send_benchmark_email.py` with OpenAI/Anthropic support
  - `LLM_PROVIDER` variable: "openai" (default) or "anthropic"
  - `EMAIL_LANGUAGE` variable: "de" (default), "en", "es", "fr"
  - GPT-4o-mini / Claude-3.5-haiku analyze benchmark data and generate contextual summaries
  - Fallback to static template if LLM unavailable

- **Gmail Draft Automation Enhancements** (2026-01-17)
  - PNG chart attachments in benchmark report emails
  - Proper UTF-8 encoding for German umlauts (ü, ö, ä, ß)
  - MIME multipart email construction with inline images

### Fixed
- **Notebook 11 JSON Encoding** (2026-01-26)
  - Fixed invalid control characters in `11_CRUD_Playground.ipynb`
  - Raw 0x0A bytes replaced with proper escaped newlines
  - Resolves mkdocs-jupyter build failures

- **Billing System: Time Entry Parsing**
  - Switched from REST Notes API to GraphQL API for time tracking
  - `spent_at` dates now correctly captured (was showing note creation date)
  - `generate_timesheet.py` properly consolidates entries per day

- **Billing Automation: Scheduled Pipeline**
  - Added `generate_timesheets` CI job for automated monthly generation
  - Created scheduled pipeline (1st of month at 6am Vienna time)
  - Workflow rules now support `schedule` pipeline source
  - Manual trigger available with `GENERATE_TIMESHEETS=true` variable

- **GCP K8s Runner: Kubeconfig Permissions** (2026-01-17)
  - K3s kubeconfig now properly configured for gitlab-runner user
  - Explicit `--kubeconfig` path resolves permission issues
  - Runner can now execute Kubernetes jobs on GCP VM

### Added
- **Voice Roundtrip Notebook (17)** (2026-01-26)
  - Cross-platform voice input testing notebook for local machines
  - Audio recording via `sounddevice` (Mac/Windows/Linux)
  - Whisper API transcription with reservoir domain vocabulary
  - Rule-based + LLM intent parsing (Claude/GPT-4 fallback)
  - 10 test utterances for validation
  - Ref: ADR-028

- **Intent Taxonomy** (`src/clarissa/agent/intents/taxonomy.json`)
  - 6 categories: simulation_control, well_operations, schedule_operations, query_operations, validation, help_and_info
  - 22 distinct intents with examples, required/optional entities, ECLIPSE keyword mappings
  - 17 entity type definitions with validation patterns
  - Confidence thresholds per intent

- **NLP Pipeline Protocols** (`src/clarissa/agent/pipeline/protocols.py`)
  - `StageResult` dataclass with validation invariants
  - 7 stage Protocols: SpeechRecognizer, IntentRecognizer, EntityExtractor, AssetValidator, SyntaxGenerator, DeckValidator, PipelineController
  - Runtime-checkable for isinstance() support

- **Intent Recognition Stage** (`src/clarissa/agent/pipeline/intent.py`)
  - RuleBasedRecognizer with 22 intent patterns
  - HybridRecognizer (rules + LLM fallback)
  - Factory function `create_recognizer()`
  - Confidence scoring and alternatives

- **Entity Extraction Stage** (`src/clarissa/agent/pipeline/entities.py`)
  - 8 entity types: wells, rates, pressures, dates, durations, fluids, well types, grid locations
  - Unit conversion utilities (RateValue, PressureValue)
  - Required/optional entity validation per intent

- **Validation Checkpoint Framework** (`src/clarissa/agent/pipeline/validation.py`)
  - Three-state decision pattern: PROCEED, CLARIFY, ROLLBACK/FAIL
  - Per-stage threshold configuration via `StageThresholds`
  - Clarification prompt generation
  - Decision history tracking and summary
  - Factory: `create_checkpoint(strict=True)`

- ADR-011: OPM Flow Simulator Integration
- `SimulatorAdapter` abstract base class in `src/clarissa/simulators/base.py`
- `OPMFlowAdapter` for OPM Flow integration via Docker
- OPM Flow Docker infrastructure in `src/clarissa/simulators/opm/`
- Integration test suite for OPM Flow (`tests/integration/test_opm_flow.py`)

### Changed
- `MockSimulator` now inherits from `SimulatorAdapter` ABC
- Extended contract tests to verify inheritance and optional fields
- `.gitignore` extended for OPM/ECLIPSE output artifacts

### Removed
- Standalone `opmflow/` directory (migrated to `src/clarissa/simulators/opm/`)

---

### Previously in Unreleased
- ADR-009: Multi-Stage NLP Translation Pipeline (Proposed)
- IJACSA 2026 paper draft with architecture diagrams (`conference/ijacsa-2026/`)
- Extracted version history from README into CHANGELOG.md

---

## [0.3.0] - 2025-12-28

### Added
- **Voice Roundtrip Notebook (17)** (2026-01-26)
  - Cross-platform voice input testing notebook for local machines
  - Audio recording via `sounddevice` (Mac/Windows/Linux)
  - Whisper API transcription with reservoir domain vocabulary
  - Rule-based + LLM intent parsing (Claude/GPT-4 fallback)
  - 10 test utterances for validation
  - Ref: ADR-028

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
- **Voice Roundtrip Notebook (17)** (2026-01-26)
  - Cross-platform voice input testing notebook for local machines
  - Audio recording via `sounddevice` (Mac/Windows/Linux)
  - Whisper API transcription with reservoir domain vocabulary
  - Rule-based + LLM intent parsing (Claude/GPT-4 fallback)
  - 10 test utterances for validation
  - Ref: ADR-028

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
- **Voice Roundtrip Notebook (17)** (2026-01-26)
  - Cross-platform voice input testing notebook for local machines
  - Audio recording via `sounddevice` (Mac/Windows/Linux)
  - Whisper API transcription with reservoir domain vocabulary
  - Rule-based + LLM intent parsing (Claude/GPT-4 fallback)
  - 10 test utterances for validation
  - Ref: ADR-028

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