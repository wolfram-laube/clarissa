# CLARISSA

**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

---

CLARISSA bridges natural language interaction and domain-specific simulation syntax through governed, simulator-in-the-loop learning.


!!! success "🎤 NEW: Voice Input"
    Control CLARISSA by voice! Say *"Show me the permeability"* or *"What's the water cut?"*
    
    [:fontawesome-solid-microphone: **Try Live Demo →**](demos/voice-demo.html){ .md-button .md-button--primary }
    [:fontawesome-solid-book: **Tutorial**](tutorials/guides/voice-input-tutorial.md){ .md-button }


## 🚀 Neu hier? Start Here!

<div class="grid cards" markdown>

-   :material-rocket-launch: **Getting Started Guide**

    Installation, erster Start, Pipeline triggern, Deployment - alles in 15 Minuten.
    
    [:fontawesome-solid-rocket: **🇬🇧 English**](getting-started-en.md){ .md-button .md-button--primary }
    [:fontawesome-solid-rocket: **🇩🇪 Deutsch**](getting-started-de.md){ .md-button }

-   :material-presentation-play: **Interactive Workflow Guide**

    Learn the GitLab workflow in 5 minutes with our interactive slides.
    
    [:fontawesome-solid-play: **Start Slides →**](guides/contributing/index.html){ .md-button }

-   :material-file-document-outline: **Quick Reference**

    Cheatsheet for branch naming, commits, and merge requests.
    
    [🇬🇧](guides/contributing/cheatsheet-en.md) | [🇩🇪](guides/contributing/cheatsheet-de.md) | [🇻🇳](guides/contributing/cheatsheet-vi.md) | [🇸🇦](guides/contributing/cheatsheet-ar.md) | [🇮🇸](guides/contributing/cheatsheet-is.md)

</div>

---

## Was kann ich tun? / What can I do?

| I want to... / Ich will... | Guide |
|-------------|-----------|
| **🎤 Try Voice Control** | [Live Demo](demos/voice-demo.html) / [Tutorial](tutorials/guides/voice-input-tutorial.md) |
| Install & run CLARISSA | [🇬🇧 Getting Started](getting-started-en.md) / [🇩🇪 Erste Schritte](getting-started-de.md) |
| Contribute code | [Contributing Guide](contributing.md) |
| Understand CI pipeline | [CI Guide](ci/README.md) |
| Manage runners (Start/Stop) | [🇬🇧 Runner Management](runner-management-en.md) / [🇩🇪 Runner Verwaltung](runner-management-de.md) |
| Understand architecture | [Architecture Overview](architecture/README.md) |
| Edit papers/publications | [Publications](publications/index.md) |

---

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
| [Publications](publications/index.md) | Research papers, PDFs, editing guides |
| [CI/CD Guide](ci/README.md) | Understanding pipeline results |
| [Runner Management](runner-management-en.md) | Start/Stop Runner, GCP VM Management |
| [Simulator Adapters](simulators/adapter_matrix.md) | Supported simulators and status |

## Project Status

CLARISSA is currently in **Phase 0** development, focusing on:

- NLP translation pipeline architecture
- Governance framework design  
- OPM Flow integration via Docker
- CI/CD infrastructure

---

*Built by BlauWeiss LLC | [GitLab Repository](https://gitlab.com/wolfram_laube/blauweiss_llc/irena)*
