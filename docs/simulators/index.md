# Simulators Documentation

CLARISSA integrates with reservoir simulation engines to validate generated syntax 
and provide physics-in-the-loop learning per ADR-001.

## Overview

```
┌─────────────────────┐
│   NLP Pipeline      │
│   (Intent → Syntax) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SimulatorAdapter   │  ← Abstract interface (ADR-011)
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌─────────┐
│OPM Flow │  │  Mock   │
│(Docker) │  │Simulator│
└─────────┘  └─────────┘
```

## Supported Simulators

| Simulator | Status | Backend | Notes |
|-----------|--------|---------|-------|
| **OPM Flow** | ✅ Production | Docker | Open-source, full ECLIPSE syntax |
| **MockSimulator** | ✅ Testing | In-memory | Contract test reference |
| MRST | 🔜 Planned | MATLAB/Octave | Research-focused |
| ECLIPSE | 📋 Future | License req. | Commercial, full-featured |

## Quick Links

- [Adapter Contract](adapter-contract.md) - Interface specification
- [Adapter Matrix](adapter_matrix.md) - Detailed capability comparison
- [OPM Flow Guide](opm-flow.md) - Docker setup and usage
- [Kubernetes Jobs](k8s-jobs.md) - Production deployment

## Architecture Decisions

- **ADR-001**: Physics-Centric, Simulator-in-the-Loop Architecture
- **ADR-004**: Dual Simulator Strategy (OPM + Mock)
- **ADR-011**: OPM Flow Simulator Integration
- **ADR-012**: Container Registry and K8s Deployment Strategy

## Adding a New Simulator

To integrate a new simulation engine:

1. **Implement `SimulatorAdapter`** - See [adapter-contract.md](adapter-contract.md)
2. **Create Docker image** (if applicable)
3. **Add to CI/CD** - Container registry push
4. **Write tests** - Contract tests + integration tests
5. **Document** - Add to this section

Example skeleton:

```python
from clarissa.simulators.base import SimulatorAdapter, SimulatorResult

class MySimulatorAdapter(SimulatorAdapter):
    def run(self, case: str) -> SimulatorResult:
        # Execute simulation
        # Parse output
        return SimulatorResult(
            converged=True,
            errors=[],
            metrics={"runtime_seconds": 42.5},
            artifacts={"output": "/path/to/results"}
        )
```