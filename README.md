# CLARISSA  
**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

CLARISSA is a research-driven system for **governed, simulator-in-the-loop reasoning**.
It combines physics-based simulation, learning signals, and human-in-the-loop governance
into a single, coherent architecture.

Architecture is not implicit in code.  
It is **explicitly documented and versioned**.

---

## 📚 Documentation

**[→ Full Documentation (GitLab Pages)](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/)**

| Quick Links | |
|-------------|---|
| [Contributing Guide](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/contributing/) | How to contribute |
| [Workflow Slides](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/guides/contributing/) | Interactive 5-min intro |
| [Project Management](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/guides/project-management/) | Issues, Labels, Boards |
| [CI Guide](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/ci/) | How to read CI results |
| [ADRs](https://wolfram_laube.gitlab.io/blauweiss_llc/irena/architecture/adr/) | Architecture decisions |

---

## What This Repository Is

This repository is the **single source of truth** for:

- the CLARISSA codebase
- architectural decisions (ADRs)
- CI philosophy as an observability layer
- simulator adapter contracts
- reproducible research artifacts

Architecture Decision Records (ADRs) are **first-class artifacts**.
They define the architectural baseline of the project.

---

## Repository Structure (High Level)

```text
src/clarissa/           # Core CLARISSA package (agent, governance, learning, CLI)
src/clarissa_kernel/    # Native simulation kernel and learning signals

docs/                   # Architecture, ADRs, and technical documentation
docs/architecture/adr/  # Architecture Decision Records (source of truth)
docs/ci/                # CI philosophy and automation documentation
docs/simulators/        # Simulator adapter matrix and notes

scripts/                # Operational and CI tooling
tests/                  # Contract tests, golden CLI tests, governance checks
