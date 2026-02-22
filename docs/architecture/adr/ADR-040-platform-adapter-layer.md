# ADR-040: Platform Adapter Layer (PAL) — Pluggable Backend Architecture

| Status | **Accepted** |
|--------|-------------|
| Date | 2026-02-22 |
| Authors | Wolfram Laube |
| Supersedes | — |
| Related | ADR-024 (Core Architecture), ADR-038 (Sim-Engine), ADR-011 (OPM Flow) |
| Epic | #161 (CLARISSA Real Reservoir Simulation Engine) |
| Issues | #162, #163, #164, #165, #166, #172 |

---

## Context

CLARISSA requires integration with multiple, fundamentally different reservoir
simulators — each with its own input formats, execution models, and output
structures. Currently OPM Flow (Eclipse-compatible, open source) and MRST
(MATLAB/Octave-based, academic) are targeted, with commercial simulators
(Schlumberger ECLIPSE, CMG) as potential future additions.

Without an abstraction layer, each simulator integration would be a
standalone implementation with its own API contract, test harness, and
deployment model. This leads to code duplication, divergent interfaces,
and the impossibility of cross-simulator comparison — which is the core
scientific value proposition of CLARISSA.

### Architectural Provenance

The Platform Adapter Layer draws directly from the **ICE (Infrastructure
Cloud Engine) v2.1 architecture** designed by the author for the Elia Group /
50Hertz EDP Platform (2024). In ICE, heterogeneous infrastructure backends
(compute, storage, network across private and public clouds) are abstracted
behind a unified adapter contract with:

- **Typed adapters** with a common ABC (`ResourceAdapter`)
- **Registry-based discovery** (`AdapterRegistry`)
- **Health/info contract** per adapter for observability
- **Backend-agnostic result format** for the orchestration layer

The key insight from ICE was: **the abstraction boundary must sit at the
result format, not the input format**. Each backend has fundamentally
different input requirements (Terraform vs. Ansible vs. CloudFormation in
ICE; Eclipse .DATA vs. MRST .m scripts in CLARISSA), but the *consumer* of
results needs a uniform contract. The PAL in CLARISSA applies this same
principle: heterogeneous input generation per backend, unified
`UnifiedResult` output.

| ICE v2.1 (Elia/50Hertz) | CLARISSA PAL |
|--------------------------|-------------|
| `ResourceAdapter` (ABC) | `PlatformAdapter` (ABC) |
| `ComputeAdapter`, `StorageAdapter`, `NetworkAdapter` | `SimulatorBackend`, `EvidenceProvider`, `EventBus` |
| `AdapterRegistry` | `AdapterRegistry` (identical pattern) |
| `healthy()` + `info()` | `healthy()` + `info()` (identical contract) |
| Terraform / Ansible / CF → Provisioned Resource | Eclipse .DATA / MRST .m → `UnifiedResult` |
| Hybrid Cloud (private + AWS/Azure/GCP) | Multi-Simulator (OPM + MRST + commercial) |

This is not coincidental similarity — it is the same architectural pattern
applied by the same architect to an analogous problem domain.

---

## Decision

### 1. PlatformAdapter ABC

All pluggable components in CLARISSA extend `PlatformAdapter`:

```python
class PlatformAdapter(ABC):
    adapter_type: str = "generic"  # Override per subclass category

    @property
    @abstractmethod
    def name(self) -> str: ...      # Unique within adapter_type

    def healthy(self) -> bool: ...   # Operational check
    def info(self) -> dict: ...      # Metadata for discovery
```

**Design principles:**
- Minimal contract: `name` + `healthy()` + `info()` — nothing more at the base level
- `adapter_type` as class variable, not instance — all OPM backends are type `"simulator"`
- Default implementations for `healthy()` (True) and `info()` — override for real checks
- No framework dependencies in the ABC itself (pure Python + `abc`)

### 2. Adapter Type Hierarchy

```
PlatformAdapter (ABC)
├── SimulatorBackend (ABC)          adapter_type = "simulator"
│   ├── OPMBackend                  name = "opm"        ✅ Phase A
│   ├── MRSTBackend                 name = "mrst"       🔲 Phase B (#166)
│   └── MockBackend                 name = "mock"       ✅ Testing
│
├── EvidenceProvider (ABC)          adapter_type = "evidence"
│   ├── WeatherProvider             name = "weather"     ✅ Dialectic
│   ├── SimResultProvider           name = "sim_result"  🔲 #170
│   └── ...
│
└── EventBus (ABC)                  adapter_type = "event"
    ├── PubSubBus                   name = "pubsub"      🔲 #171
    └── InMemoryBus                 name = "memory"      🔲 Testing
```

Each category ABC extends `PlatformAdapter` with domain-specific methods:

| Category | Additional Contract | Input → Output |
|----------|-------------------|----------------|
| `SimulatorBackend` | `validate()`, `run()`, `parse_result()` | `SimRequest` → `UnifiedResult` |
| `EvidenceProvider` | `gather()`, `confidence()` | Query → Evidence + Score |
| `EventBus` | `publish()`, `subscribe()` | Event → Subscribers |

### 3. AdapterRegistry

Central registry with type-safe discovery:

```python
registry = AdapterRegistry()
registry.register(OPMBackend())
registry.register(MRSTBackend())

# Discovery
backend = registry.get("simulator", "opm")     # → OPMBackend
names = registry.list_names("simulator")        # → ["opm", "mrst"]
health = registry.health()                      # → {"healthy": True, "adapters": {...}}
```

**Registry properties:**
- Thread-safe singleton per process (lazy initialization)
- Last-write-wins for duplicate `type + name` (explicit overwrite, logged)
- Health aggregation: `registry.healthy` is False if *any* adapter is unhealthy
- Info endpoint: returns all adapter metadata for `/health` API responses
- No auto-discovery magic — adapters must be explicitly registered

### 4. SimulatorBackend Contract (Detail)

The simulator-specific contract extends `PlatformAdapter` with three phases:

```
Phase 1: validate(request) → list[str]     # Empty = valid
Phase 2: run(request, work_dir, on_progress) → dict  # Raw backend output
Phase 3: parse_result(raw, request) → UnifiedResult   # Unified format
```

**Critical design choice: asymmetric I/O.**

Input is backend-specific (Eclipse .DATA for OPM, .m script for MRST),
generated by backend-specific code. Output is always `UnifiedResult` —
the PAL boundary sits here:

```
                    PAL Boundary
                         │
SimRequest ──► [Backend] ─┤──► UnifiedResult (Pydantic)
                         │
  OPM: .DATA → flow     │    Identical JSON contract
  MRST: .m → octave     │    for all consumers
  Mock: in-memory        │
```

The `UnifiedResult` Pydantic model is the **contract surface** — any
simulator that can produce it is a valid PAL adapter. This is the same
principle as ICE's unified resource representation regardless of
provisioning backend.

### 5. Backend Lifecycle

```
┌─────────┐     register()     ┌──────────┐
│ Backend  │──────────────────►│ Registry │
│ Instance │                   └────┬─────┘
└─────────┘                        │
                                   │ get("simulator", "opm")
                                   ▼
                            ┌──────────┐
                            │ Consumer │  (sim_api, delta_engine, ...)
                            └──────────┘
```

1. **Instantiation**: Backend is created with optional config
2. **Registration**: `register_backend(backend)` adds to registry
3. **Discovery**: `get_backend("opm")` retrieves by name
4. **Validation**: `backend.validate(request)` before execution
5. **Execution**: `backend.run(request, work_dir, on_progress)`
6. **Parsing**: `backend.parse_result(raw, request)` → `UnifiedResult`
7. **Health**: `backend.healthy()` checked periodically

### 6. File Structure

```
src/clarissa/
├── pal/                          # Platform Adapter Layer (generic)
│   ├── __init__.py               # Exports: PlatformAdapter, AdapterRegistry
│   ├── base.py                   # PlatformAdapter ABC
│   └── registry.py               # AdapterRegistry
│
└── sim_engine/                   # Simulator-specific PAL specialization
    ├── __init__.py               # Public API
    ├── models.py                 # SimRequest, UnifiedResult, etc.
    ├── deck_generator.py         # Eclipse .DATA generation
    ├── sim_api.py                # FastAPI service
    ├── Dockerfile                # OPM Flow container
    └── backends/
        ├── __init__.py           # Exports + registry functions
        ├── base.py               # SimulatorBackend(PlatformAdapter)
        ├── registry.py           # Simulator-specific registry wrapper
        ├── opm_backend.py        # OPM Flow implementation
        └── mrst_backend.py       # MRST/Octave implementation (Phase B)
```

---

## Consequences

### Positive

- **Backend-agnostic consumers**: The FastAPI service, Delta Engine (#167),
  and future Portal integration (#168) work identically regardless of
  which simulator produced the result
- **Cross-validation enabled**: Running the same `SimRequest` through OPM
  and MRST and comparing `UnifiedResult` objects is the core CLARISSA value
- **Testability**: `MockBackend` for fast unit tests, real backends for
  integration tests — same interface
- **Extensibility**: Adding a commercial simulator (ECLIPSE, CMG) requires
  only implementing `SimulatorBackend` — no changes to consumers
- **Architectural clarity**: The ICE-proven pattern provides confidence
  that the abstraction holds under production load

### Negative

- **Lowest common denominator**: `UnifiedResult` can only contain data that
  all simulators can produce. Simulator-specific advanced features (e.g.,
  OPM's compositional modeling) need extension points
- **Abstraction leaks**: Eclipse deck format assumptions may bleed into the
  `SimRequest` model. MRST may need different parameterization that doesn't
  map cleanly
- **Registry overhead**: For a system with 2-3 backends, the registry is
  over-engineered. It pays off only if the pattern extends to other adapter
  types (evidence, events)

### Mitigations

- `UnifiedResult` has an `extras: dict` field for backend-specific data
- `SimRequest` uses generic `FluidProperties` that map to both Eclipse
  keywords and MRST parameters
- The registry is already used for evidence providers (Dialectic Engine),
  validating the multi-type pattern

---

## Compliance

| Criterion | Status |
|-----------|--------|
| ICE v2.1 §3.2.12 alignment | ✅ Same patterns, same architect |
| ADR-024 Core Architecture | ✅ PAL is the "Simulator-Agnostic" layer |
| ADR-038 Sim-Engine | ✅ SimulatorBackend extends PlatformAdapter |
| GOV-001 test coverage | ✅ 90+ sim_engine tests, PAL tests in contracts |
| Pydantic models | ✅ SimRequest, UnifiedResult fully typed |

---

## References

- ICE v2.1 Architecture (Elia Group / 50Hertz EDP Platform, 2024) — §3.2.12 Resource Adapter Pattern
- ADR-024: CLARISSA Core System Architecture
- ADR-038: Sim-Engine Architecture
- Epic #161: CLARISSA Real Reservoir Simulation Engine
- Issue #172: PAL — Platform Adapter Layer
