# CLARISSA  
**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

CLARISSA is a research-driven system for **governed, simulator-in-the-loop reasoning**.
It combines physics-based simulation, learning signals, and human-in-the-loop governance
into a single, coherent architecture.

Architecture is not implicit in code.  
It is **explicitly documented and versioned**.

---

## 🚀 New Contributor?

**[▶️ Start the Interactive Workflow Guide](https://irena-40cc50.gitlab.io/guides/contributing/)** — Learn our GitLab workflow in 5 minutes!

---

## 📚 Documentation

**[→ Full Documentation (GitLab Pages)](https://irena-40cc50.gitlab.io/)**

| Quick Links | |
|-------------|---|
| [Contributing Guide](https://irena-40cc50.gitlab.io/contributing/) | How to contribute |
| [Workflow Slides](https://irena-40cc50.gitlab.io/guides/contributing/) | Interactive 5-min intro |
| [Project Management](https://irena-40cc50.gitlab.io/guides/project-management/) | Issues, Labels, Boards |
| [CI Guide](https://irena-40cc50.gitlab.io/ci/) | How to read CI results |
| [ADRs](https://irena-40cc50.gitlab.io/architecture/adr/) | Architecture decisions |
| [Publications](https://irena-40cc50.gitlab.io/publications/) | Research papers (IJACSA 2026) |
| [Billing](https://irena-40cc50.gitlab.io/guides/billing/) | Time tracking & invoicing |

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
```
