# ADR-011 — OPM Flow Simulator Integration

## Status
Proposed

## Context

Ian contributed a standalone Docker setup for OPM Flow in the `opmflow/` directory.
This provides working infrastructure for running the open-source reservoir simulator, including:

- Dockerfile based on Ubuntu 22.04 with OPM packages from the official PPA
- docker-compose configuration for local development
- Sample SPE1CASE1 test case with output artifacts
- Documentation for standalone usage

However, this implementation exists as an isolated component within the repository:

1. **No adapter interface**: The setup lacks the contract defined in `docs/simulators/adapter_matrix.md`
   requiring `run(case) -> {converged, errors, metrics?, artifacts?}`.
2. **Architectural disconnect**: Code in `opmflow/` has no connection to `src/clarissa/simulators/`.
3. **Repository hygiene issues**: Output files (`.EGRID`, `.INIT`, `.PRT`) committed to repo;
   duplicate test data files exist.

Per ADR-001, simulators are "first-class learning substrates" requiring proper integration
into CLARISSA's feedback loop. The current standalone structure prevents OPM Flow from
participating in the learning and governance cycles.

## Decision

Refactor the OPM Flow integration from a standalone directory into the CLARISSA simulator
module structure:

```
src/clarissa/simulators/
├── __init__.py
├── base.py                  # SimulatorAdapter ABC (new)
├── mock.py                  # existing MockSimulator
└── opm/
    ├── __init__.py
    ├── adapter.py           # OPMFlowAdapter implementing contract
    ├── Dockerfile           # moved from opmflow/
    ├── docker-compose.yml   # moved from opmflow/
    └── entrypoint.sh        # moved from opmflow/

tests/
├── contracts/
│   └── test_simulator_contract.py  # extended for OPM
└── integration/
    └── test_opm_flow.py            # new integration tests
```

The `opmflow/` directory will be removed after migration.
Output artifacts and duplicate data files will be excluded via `.gitignore`.

## Rationale

1. **Alignment with ADR-001**: Simulators belong in the core module as learning substrates,
   not as isolated infrastructure artifacts.

2. **Contract enforcement**: The adapter pattern ensures OPM Flow returns standardized
   feedback (`converged`, `errors`, `metrics`) for CLARISSA's learning loop.

3. **Co-location principle**: Adapter code and its Docker infrastructure belong together—
   changes to one often require changes to the other.

4. **Extensibility**: This pattern serves as a template for future simulator backends
   (MRST, commercial simulators via file-based interfaces).

5. **Testability**: Contract tests can verify OPM adapter behavior alongside MockSimulator,
   enabling CI validation without requiring full simulation runs.

## Consequences

### Positive
- OPM Flow becomes a first-class CLARISSA component participating in learning cycles.
- Clear contract enables CI integration and standardized feedback parsing.
- Pattern established for additional simulator backends.
- Ian's infrastructure work is preserved and properly integrated.

### Negative
- Migration requires careful commit sequence to preserve git history attribution.
- Adapter implementation adds code surface that must be maintained.
- Docker build adds CI complexity (image caching, registry decisions).

### Neutral / Open
- Docker image build/push strategy for CI to be determined separately.
- Decision on test data location (keep SPE1 in repo vs. download on demand) deferred.
- MPI parallelization support in adapter interface not yet specified.

## Alternatives Considered

### Option B: Separate infrastructure directory
```
infrastructure/docker/opm-flow/
src/clarissa/simulators/opm/adapter.py  # references infrastructure/
```
**Rejected**: Splits coupled concerns across distant directories; violates proximity principle;
makes it harder to reason about adapter-infrastructure dependencies.

### Option C: Keep opmflow/ as-is, add adapter separately
**Rejected**: Perpetuates architectural debt; creates unclear ownership; likely leads to
duplicate Docker configurations or drift between standalone and integrated versions.

## Implementation Notes

- Use Conventional Commits: `refactor:` for moves, `feat:` for adapter implementation
- Update CHANGELOG.md under appropriate version section
- Extend `.gitignore` for OPM output artifacts (`.PRT`, `.EGRID`, `.INIT`, `.DBG`)
- Consider preserving git history via `git mv` where possible

## Related ADRs
- ADR-001 — Physics-Centric, Simulator-in-the-Loop Architecture
- ADR-003 — CLARISSA-Native Simulation Kernel
- ADR-004 — Dual-Simulator Strategy (Superseded)
