# ADR-024: CLARISSA Core System Architecture

| Status | Proposed |
|--------|----------|
| Date | 2026-01-22 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-021 (Portal System), ADR-011 (OPM Flow Integration) |

---

## Context

CLARISSA is a Conversational AI System for Reservoir Simulation. The previous ADRs (021-023) describe the Admin Portal. This ADR defines the **Core System Architecture** - the actual heart of the system.

### Requirements

1. **Modular Microservices**: Independently deployable, scalable
2. **Flexible Communication**: REST (external), gRPC (internal), Message Broker (async)
3. **Simulator-Agnostic**: Abstraction layer for OPM Flow, MRST, (later: commercial)
4. **Service Clustering**: Related microservices grouped together

---

## Decision

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLARISSA Core System                                │
│                                                                                  │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                              External Interface                                  │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                                                                                  │
│      Web UI          Voice API         REST API         gRPC API                │
│         │                │                 │                │                   │
│         └────────────────┴────────┬────────┴────────────────┘                   │
│                                   │                                              │
│                                   ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                         API Gateway / BFF                                   │ │
│  │                                                                             │ │
│  │   • Routing & Load Balancing                                               │ │
│  │   • Authentication / Authorization                                          │ │
│  │   • Rate Limiting                                                          │ │
│  │   • Protocol Translation (REST ↔ gRPC)                                     │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                   │                                              │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                              Service Clusters                                    │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                                   │                                              │
│         ┌─────────────────────────┼─────────────────────────┐                   │
│         │                         │                         │                   │
│         ▼                         ▼                         ▼                   │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐             │
│  │ Conversation│          │ Simulation  │          │  Analysis   │             │
│  │   Cluster   │◄────────►│   Cluster   │◄────────►│   Cluster   │             │
│  │             │  gRPC /  │             │  gRPC /  │             │             │
│  │             │  Events  │             │  Events  │             │             │
│  └─────────────┘          └─────────────┘          └─────────────┘             │
│                                   │                                              │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                         Simulator Abstraction Layer                              │
│  ═══════════════════════════════════════════════════════════════════════════    │
│                                   │                                              │
│                    ┌──────────────┼──────────────┐                              │
│                    │              │              │                              │
│                    ▼              ▼              ▼                              │
│             ┌──────────┐   ┌──────────┐   ┌──────────┐                         │
│             │ OPM Flow │   │   MRST   │   │  Future  │                         │
│             │ Adapter  │   │ Adapter  │   │ Adapters │                         │
│             └──────────┘   └──────────┘   └──────────┘                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Clusters

### Principle: Bounded Context

Microservices that belong together functionally are grouped into **Clusters**:
- **Within** a cluster: Message Broker (Tight Coupling OK)
- **Between** clusters: gRPC or Events (Loose Coupling)
- **External**: REST API via Gateway

### Cluster 1: Conversation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Conversation Cluster                          │
│                                                                  │
│   Responsibility: NLP, Dialog Management, User Intent            │
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │ NLP Parser  │   │   Intent    │   │   Dialog    │          │
│   │             │──►│ Classifier  │──►│  Manager    │          │
│   │ • Tokenize  │   │             │   │             │          │
│   │ • NER       │   │ • Classify  │   │ • State     │          │
│   │ • Parse     │   │ • Params    │   │ • Response  │          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐                             │
│   │  Context    │   │   Session   │                             │
│   │   Store     │   │   Manager   │                             │
│   └─────────────┘   └─────────────┘                             │
│                                                                  │
│   Exposed gRPC:                                                  │
│   • ProcessUtterance(text) → Intent + Entities                  │
│   • GetDialogState(session_id) → State                          │
│   • GenerateResponse(intent, context) → Response                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cluster 2: Simulation

```
┌─────────────────────────────────────────────────────────────────┐
│                     Simulation Cluster                           │
│                                                                  │
│   Responsibility: Deck Generation, Job Management, Execution     │
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │    Deck     │   │    Deck     │   │     Job     │          │
│   │  Generator  │──►│  Validator  │──►│ Orchestrator│          │
│   │             │   │             │   │             │          │
│   │ • NL→Deck   │   │ • Syntax    │   │ • Queue     │          │
│   │ • Templates │   │ • Physics   │   │ • Schedule  │          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│                                              │                   │
│                                              ▼                   │
│                                 ┌─────────────────────┐         │
│                                 │   Job Runner Pool   │         │
│                                 │  ┌───┐ ┌───┐ ┌───┐ │         │
│                                 │  │ W │ │ W │ │ W │ │         │
│                                 │  └───┘ └───┘ └───┘ │         │
│                                 └─────────────────────┘         │
│                                              │                   │
│                              Simulator Abstraction Layer         │
│                                                                  │
│   Events: job.submitted, job.started, job.completed, job.failed │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cluster 3: Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                      Analysis Cluster                            │
│                                                                  │
│   Responsibility: Results Processing, Visualization, Reporting   │
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │   Results   │   │ Comparison  │   │Visualization│          │
│   │   Parser    │──►│   Engine    │──►│   Service   │          │
│   │             │   │             │   │             │          │
│   │ • SMSPEC    │   │ • Diff      │   │ • Charts    │          │
│   │ • UNSMRY    │   │ • History   │   │ • 3D Grid   │          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐                             │
│   │  Reporting  │   │   Export    │                             │
│   │   Engine    │   │   Service   │                             │
│   └─────────────┘   └─────────────┘                             │
│                                                                  │
│   Events Consumed: job.completed → Trigger auto-parsing          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Communication Patterns

### When to Use Which Medium?

| Medium | Use Case | Example |
|--------|----------|---------|
| **REST** | External API, CRUD | User → Gateway |
| **gRPC** | Internal, High-Perf, Streaming | Cluster ↔ Cluster |
| **Message Broker** | Async, Events, Decoupled | Job Events |

### Message Broker Topics

```
clarissa/
├── jobs/
│   ├── submitted    # { job_id, deck_hash, user_id }
│   ├── started      # { job_id, worker_id, simulator }
│   ├── progress     # { job_id, step, total }
│   ├── completed    # { job_id, duration_s, result_path }
│   └── failed       # { job_id, error, retry_count }
│
├── conversation/
│   ├── utterance    # { session_id, text }
│   └── response     # { session_id, text, actions }
│
└── analysis/
    ├── parsed       # { job_id, summary_stats }
    └── report       # { job_id, report_url }
```

---

## Simulator Abstraction Layer (SAL)

### Motivation

CLARISSA should **not** be bound to a single simulator:

| Simulator | Strength | Use Case |
|-----------|----------|----------|
| **OPM Flow** | Production-ready, Eclipse-compatible | Full-field, History Match |
| **MRST** | Flexible, MATLAB, Rapid Prototyping | Research, Sensitivities |
| *Eclipse* | Industry Standard (proprietary) | Client Validation |
| *CMG* | Thermal, Heavy Oil (proprietary) | Special Cases |

### Interface Definition

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator

class SimulatorBackend(Enum):
    OPM_FLOW = "opm_flow"
    MRST = "mrst"
    # Future: ECLIPSE, CMG

class SimulatorInterface(ABC):
    """Abstract interface for reservoir simulators."""
    
    @property
    @abstractmethod
    def backend(self) -> SimulatorBackend:
        """Which backend this adapter implements."""
        ...
    
    @abstractmethod
    async def submit_job(self, deck: str, config: dict) -> JobHandle:
        """Submit simulation job, return handle for tracking."""
        ...
    
    @abstractmethod
    async def get_status(self, job: JobHandle) -> JobStatus:
        """Get current job status."""
        ...
    
    @abstractmethod
    async def cancel_job(self, job: JobHandle) -> bool:
        """Cancel running job."""
        ...
    
    @abstractmethod
    async def get_results(self, job: JobHandle) -> AsyncIterator[bytes]:
        """Stream result files."""
        ...
    
    @abstractmethod
    async def validate_deck(self, deck: str) -> ValidationResult:
        """Validate deck syntax and semantics."""
        ...
    
    @abstractmethod
    def get_capabilities(self) -> SimulatorCapabilities:
        """What this simulator supports."""
        ...
```

### OPM Flow Adapter

```python
class OPMFlowAdapter(SimulatorInterface):
    """
    Adapter for OPM Flow simulator.
    - Eclipse-format decks (.DATA)
    - HPC capable, production-ready
    """
    
    @property
    def backend(self) -> SimulatorBackend:
        return SimulatorBackend.OPM_FLOW
    
    async def submit_job(self, deck: str, config: dict) -> JobHandle:
        job_id = generate_job_id()
        job_dir = self.work_dir / job_id
        
        # Write deck
        (job_dir / "MODEL.DATA").write_text(deck)
        
        # Start flow process
        process = await asyncio.create_subprocess_exec(
            "flow", str(job_dir / "MODEL.DATA"),
            f"--output-dir={job_dir}"
        )
        
        return JobHandle(job_id=job_id, backend=self.backend)
    
    def get_capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            backend=self.backend,
            physics_models=["BLACK_OIL", "COMPOSITIONAL"],
            max_cells=10_000_000,
            supports_parallel=True
        )
```

### MRST Adapter

```python
class MRSTAdapter(SimulatorInterface):
    """
    Adapter for MRST (MATLAB Reservoir Simulation Toolbox).
    - MATLAB/Octave based
    - Flexible, good for prototyping
    """
    
    @property
    def backend(self) -> SimulatorBackend:
        return SimulatorBackend.MRST
    
    async def submit_job(self, deck: str, config: dict) -> JobHandle:
        job_id = generate_job_id()
        job_dir = self.work_dir / job_id
        
        # Write deck
        (job_dir / "MODEL.DATA").write_text(deck)
        
        # Generate MRST script
        script = self._generate_mrst_script(job_dir / "MODEL.DATA")
        (job_dir / "run.m").write_text(script)
        
        # Run via Octave
        process = await asyncio.create_subprocess_exec(
            "octave", "--no-gui", "--eval", f"run('{job_dir}/run.m')"
        )
        
        return JobHandle(job_id=job_id, backend=self.backend)
    
    def _generate_mrst_script(self, deck_path: Path) -> str:
        return f"""
        mrstModule add ad-core ad-blackoil deckformat
        deck = readEclipseDeck('{deck_path}');
        [G, rock, fluid] = initEclipseModel(deck);
        [wellSols, states] = simulateScheduleAD(state0, model, schedule);
        writeEclipseOutput(states, '{deck_path.parent}/RESULTS');
        """
    
    def get_capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            backend=self.backend,
            physics_models=["BLACK_OIL", "COMPOSITIONAL", "THERMAL", "POLYMER"],
            max_cells=1_000_000,
            supports_parallel=False
        )
```

### Simulator Factory

```python
class SimulatorFactory:
    """Create simulator adapters based on requirements."""
    
    @classmethod
    def create(cls, backend: SimulatorBackend, **kwargs) -> SimulatorInterface:
        adapters = {
            SimulatorBackend.OPM_FLOW: OPMFlowAdapter,
            SimulatorBackend.MRST: MRSTAdapter,
        }
        return adapters[backend](**kwargs)
    
    @classmethod
    def get_best_backend(cls, requirements: SimRequirements) -> SimulatorBackend:
        """
        Select best backend based on requirements:
        - Quick sensitivity study → MRST (faster iteration)
        - Full-field forecast → OPM Flow (scalable)
        - Industry deliverable → OPM Flow (Eclipse-compatible)
        """
        if requirements.needs_eclipse_compatibility:
            return SimulatorBackend.OPM_FLOW
        if requirements.is_quick_study or requirements.model_type in ["thermal"]:
            return SimulatorBackend.MRST
        return SimulatorBackend.OPM_FLOW
```

---

## REST API (External)

```
/api/v1/
├── conversation/
│   ├── POST   /sessions                    # New session
│   ├── POST   /sessions/{id}/messages      # Send message
│   └── GET    /sessions/{id}/history       # Get history
│
├── simulation/
│   ├── POST   /jobs                        # Submit job
│   ├── GET    /jobs/{id}                   # Get status
│   ├── DELETE /jobs/{id}                   # Cancel
│   └── GET    /jobs/{id}/results           # Get results
│
├── analysis/
│   ├── GET    /jobs/{id}/summary           # Results summary
│   ├── POST   /compare                     # Compare runs
│   └── POST   /report                      # Generate report
│
└── decks/
    ├── POST   /generate                    # NL → Deck
    └── POST   /validate                    # Validate deck
```

---

## Deployment

### Development (Docker Compose)

```yaml
services:
  gateway:     { image: clarissa/gateway }
  conversation: { image: clarissa/conversation }
  simulation:  { image: clarissa/simulation }
  analysis:    { image: clarissa/analysis }
  broker:      { image: redis:alpine }
  opm-flow:    { image: opm/flow:latest }
  octave:      { image: gnuoctave/octave:latest }
```

### Production (Kubernetes)

```
clarissa-prod/
├── gateway (3 replicas, HPA)
├── conversation (2 replicas)
├── simulation (2 replicas)
├── analysis (2 replicas)
├── simulator-workers/
│   ├── opm-flow (0-10 replicas, autoscale)
│   └── mrst (0-5 replicas, autoscale)
└── infra/
    ├── redis (3 replicas, Sentinel)
    └── postgres (3 replicas, HA)
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Architecture** | Microservices in Bounded Context Clusters |
| **External API** | REST via API Gateway |
| **Internal Sync** | gRPC |
| **Internal Async** | Message Broker (Redis/RabbitMQ) |
| **Simulator Layer** | Abstract interface + pluggable adapters |
| **Initial Backends** | OPM Flow + MRST |

---

## References

- [ADR-011: OPM Flow Integration](./ADR-011-opm-flow-integration.md)
- [OPM Flow](https://opm-project.org/)
- [MRST - MATLAB Reservoir Simulation Toolbox](https://www.sintef.no/projectweb/mrst/)
- [gRPC Documentation](https://grpc.io/docs/)
