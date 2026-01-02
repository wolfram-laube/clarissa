# CLARISSA

**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

---

CLARISSA bridges natural language interaction and domain-specific simulation syntax through governed, simulator-in-the-loop learning.

## What is CLARISSA?

CLARISSA is a phased AI agent architecture designed to augment reservoir simulation workflows. Rather than replacing established simulators, CLARISSA integrates multiple reservoir simulators as heterogeneous sources of numerical and physical feedback.

## Core Principles

<div class="grid cards" markdown>

-   :material-brain: **Physics-Centric Learning**

    Learning flows from numerical consequences. Simulators are first-class learning substrates.
    
    [ADR-001 →](architecture/adr/ADR-001-physics-centric.md)

-   :material-shield-check: **Governed Autonomy**

    Authority flows from human approval. Clear separation of LLM reasoning, RL learning, and governance.
    
    [ADR-002 →](architecture/adr/ADR-002-separation-of-roles.md)

-   :material-cpu-64-bit: **Native Kernel**

    Physics computations in a fast, auditable native kernel—not in the LLM.
    
    [ADR-003 →](architecture/adr/ADR-003-native-kernel.md)

-   :material-swap-horizontal: **Dual-Simulator Strategy**

    OPM Flow for open-source flexibility, ECLIPSE for industry validation.
    
    [ADR-004 →](architecture/adr/ADR-004-dual-simulator-strategy.md)

</div>

## Quick Links

| Resource | Description |
|----------|-------------|
| [Architecture Overview](architecture/README.md) | System design and component interaction |
| [ADR Index](architecture/adr/index.md) | All Architecture Decision Records |
| [CI/CD Guide](ci/README.md) | Understanding pipeline results |
| [Simulator Adapters](simulators/adapter_matrix.md) | Supported simulators and status |

## Project Status

CLARISSA is currently in **Phase 0** development, focusing on:

- NLP translation pipeline architecture
- Governance framework design  
- OPM Flow integration via Docker
- CI/CD infrastructure

---

*Built by BlauWeiss LLC | [GitLab Repository](https://gitlab.com/wolfram_laube/blauweiss_llc/irena)*
