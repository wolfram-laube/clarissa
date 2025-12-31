# CLARISSA

**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

---

CLARISSA bridges natural language interaction and domain-specific simulation syntax through governed, simulator-in-the-loop learning.

## What is CLARISSA?

CLARISSA is a phased AI agent architecture designed to augment reservoir simulation workflows. Rather than replacing established simulators, CLARISSA integrates multiple reservoir simulators as heterogeneous sources of numerical and physical feedback.

<div class="grid cards" markdown>

-   :material-brain:{ .lg .middle } __Physics-Centric Learning__

    ---

    Learning flows from numerical consequences. Simulators are first-class learning substrates.

    [:octicons-arrow-right-24: ADR-001](architecture/adr/ADR-001-physics-centric.md)

-   :material-shield-check:{ .lg .middle } __Governed Autonomy__

    ---

    Authority flows from human approval. Clear separation of LLM reasoning, RL learning, and governance.

    [:octicons-arrow-right-24: ADR-002](architecture/adr/ADR-002-separation-of-roles.md)

-   :material-message-text:{ .lg .middle } __Natural Language Interface__

    ---

    Multi-stage NLP pipeline translates speech to validated simulation syntax.

    [:octicons-arrow-right-24: ADR-009](architecture/adr/ADR-009-nlp-translation-pipeline.md)

-   :material-cog:{ .lg .middle } __Configurable Deployment__

    ---

    Air-gapped or cloud-native. Same code, different configuration.

    [:octicons-arrow-right-24: Architecture Overview](architecture/overview.md)

</div>

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run interactive demo
python -m clarissa demo

# Run tests
pytest -q
```

## Core Principles

!!! quote "Design Philosophy"

    **Learning flows from numerical consequences.**  
    **Authority flows from human approval.**

1. **Physics-Centric**: Simulators provide ground truth, not text plausibility
2. **Separation of Roles**: LLM reasoning, RL learning, and governance are distinct
3. **Signals over Enforcement**: CI detects and reports; humans decide

## Project Status

| Component | Status |
|-----------|--------|
| Core Agent | ✅ Prototype |
| Governance Layer | ✅ Implemented |
| Mock Simulator | ✅ Implemented |
| NLP Pipeline | 🟡 ADR Proposed |
| OPM Flow Adapter | 🟡 Planned |
| MRST Adapter | 🟡 Planned |

## Links

- [GitLab Repository](https://gitlab.com/wolfram_laube/blauweiss_llc/irena)
- [IJACSA 2026 Paper](conference/ijacsa-2026.md)
- [Changelog](changelog.md)
