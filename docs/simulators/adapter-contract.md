# Simulator Adapter Contract

The `SimulatorAdapter` abstract base class defines the interface that all 
simulator backends must implement to participate in CLARISSA's learning loop.

## Interface Definition

```python
from abc import ABC, abstractmethod
from typing import TypedDict

class SimulatorResult(TypedDict, total=False):
    """Result structure returned by simulator adapters."""
    converged: bool        # Required: Did simulation complete?
    errors: list[str]      # Required: Error messages (empty if converged)
    metrics: dict          # Optional: Runtime stats, iterations, etc.
    artifacts: dict        # Optional: Output file paths

class SimulatorAdapter(ABC):
    """Abstract base class for simulator adapters."""
    
    @abstractmethod
    def run(self, case: str) -> SimulatorResult:
        """Execute a simulation case."""
        ...
```

## Contract Semantics

### Required Fields

| Field | Type | Invariant |
|-------|------|-----------|
| `converged` | `bool` | `True` if simulation completed successfully |
| `errors` | `list[str]` | Non-empty if `converged=False`, empty otherwise |

### Optional Fields

| Field | Type | Purpose |
|-------|------|---------|
| `metrics` | `dict[str, Any]` | Performance data, convergence info |
| `artifacts` | `dict[str, str]` | Paths to output files |

### Invariants

```python
# These invariants are enforced:
if result["converged"]:
    assert result["errors"] == []  # Success must have no errors
else:
    assert len(result["errors"]) > 0  # Failure must explain why
```

## Implementation Guidelines

### 1. Constructor

Accept configuration, don't start simulation:

```python
class OPMFlowAdapter(SimulatorAdapter):
    def __init__(
        self,
        image: str = "registry.gitlab.com/.../opm-flow:latest",
        timeout: int = 3600,
        work_dir: Path | None = None
    ):
        self.image = image
        self.timeout = timeout
        self.work_dir = work_dir or Path.cwd()
```

### 2. Input Handling

The `case` parameter can be:
- **File path**: `/path/to/CASE.DATA`
- **Deck content**: Raw ECLIPSE/OPM syntax string
- **Case name**: Resolved against a case library

```python
def run(self, case: str) -> SimulatorResult:
    if Path(case).exists():
        deck_path = Path(case)
    elif case.startswith("--"):
        # Treat as raw content
        deck_path = self._write_temp_deck(case)
    else:
        # Look up in case library
        deck_path = self.case_library / f"{case}.DATA"
```

### 3. Error Handling

Always return a valid `SimulatorResult`, never raise exceptions:

```python
def run(self, case: str) -> SimulatorResult:
    try:
        # ... run simulation ...
        return SimulatorResult(converged=True, errors=[])
    except TimeoutError:
        return SimulatorResult(
            converged=False,
            errors=["Simulation timed out after 3600s"]
        )
    except Exception as e:
        return SimulatorResult(
            converged=False,
            errors=[f"Unexpected error: {e}"]
        )
```

### 4. Metrics

Include useful metrics for learning and debugging:

```python
return SimulatorResult(
    converged=True,
    errors=[],
    metrics={
        "runtime_seconds": 142.5,
        "newton_iterations": 1523,
        "linear_iterations": 45678,
        "timesteps_completed": 365,
        "warnings_count": 3,
    }
)
```

### 5. Artifacts

Return paths to outputs for further analysis:

```python
return SimulatorResult(
    converged=True,
    errors=[],
    artifacts={
        "summary": "/output/CASE.SMSPEC",
        "restart": "/output/CASE.UNRST",
        "log": "/output/CASE.PRT",
    }
)
```

## Testing Contract Compliance

Use the contract test suite:

```python
# tests/unit/test_simulator_contract.py
import pytest
from clarissa.simulators.base import SimulatorAdapter, SimulatorResult

def test_adapter_inheritance(my_adapter):
    """Adapter must inherit from SimulatorAdapter."""
    assert isinstance(my_adapter, SimulatorAdapter)

def test_run_returns_result(my_adapter, sample_deck):
    """run() must return SimulatorResult."""
    result = my_adapter.run(sample_deck)
    assert "converged" in result
    assert "errors" in result

def test_success_has_no_errors(my_adapter, valid_deck):
    """Successful run must have empty errors."""
    result = my_adapter.run(valid_deck)
    if result["converged"]:
        assert result["errors"] == []

def test_failure_has_errors(my_adapter, invalid_deck):
    """Failed run must explain errors."""
    result = my_adapter.run(invalid_deck)
    if not result["converged"]:
        assert len(result["errors"]) > 0
```

## Existing Implementations

| Adapter | Location | Notes |
|---------|----------|-------|
| `MockSimulator` | `src/clarissa/simulators/mock.py` | Reference implementation |
| `OPMFlowAdapter` | `src/clarissa/simulators/opm/adapter.py` | Docker-based |

## See Also

- [Adapter Matrix](adapter_matrix.md) - Capability comparison
- [OPM Flow Guide](opm-flow.md) - Docker setup
- ADR-011 - Integration decision