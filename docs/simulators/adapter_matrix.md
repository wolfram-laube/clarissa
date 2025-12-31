# Simulator adapter matrix

This document tracks simulator backends CLARISSA can target and the integration surface that must remain stable.

## Adapter contract (minimum)
All simulator adapters MUST implement:

- `run(case: str) -> dict`
  - `converged: bool`
  - `errors: list[str]` (empty on convergence)
  - optional: `metrics: dict[str, float | int | str]`
  - optional: `artifacts: dict[str, str]` (paths or identifiers)

Semantics:
- If `converged == False`, `errors` MUST be non-empty.
- If `converged == True`, `errors` MUST be empty.

See tests:
- `tests/contracts/test_simulator_contract.py`

## Backends

| Backend | Type | Primary language | Strengths | Risks/limits | CLARISSA status |
|---|---|---|---|---|---|
| MockSimulator | in-repo mock | Python | deterministic, fast, CI-friendly | not physically meaningful | ✅ implemented |
| MRST (Matlab Reservoir Simulation Toolbox) | external simulator | MATLAB | huge ecosystem, research-friendly workflows | MATLAB runtime/licensing, IO glue | 🟡 planned |
| OPM Flow (Open Porous Media) | external simulator | C++ | open-source, industry-grade black-oil/compositional | integration complexity, deck management | 🟡 planned |

## Integration approach (recommended)
CLARISSA treats simulators as *pluggable backends* behind a strict contract.

### MRST adapter sketch
- CLARISSA writes a case/deck representation (or MATLAB script) into a temp workdir
- invokes MATLAB/Octave (depending on feasibility)
- parses convergence / error markers and returns a contract-compliant dict

### OPM adapter sketch
- CLARISSA writes an Eclipse-style deck (or references existing decks)
- invokes `flow` (or dockerized OPM)
- parses log convergence + reports and returns a contract-compliant dict

## Decision points
- Prefer *file-based interfaces* first (robust, auditable), then optimize into in-memory APIs.
- Keep adapter responsibilities narrow: IO + invocation + parsing + contract mapping.
- Put physical correctness into the simulator, not into CLARISSA.
