# CLARISSA  
**Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

CLARISSA is a research-driven system for **governed, simulator-in-the-loop reasoning**.
It combines physics-based simulation, learning signals, and human-in-the-loop governance
into a single, coherent architecture.

Architecture is not implicit in code.  
It is **explicitly documented and versioned**.

---

## 🚀 Neu hier? / New here?

| What you want | Where to go |
|---------------|-------------|
| **Install & run CLARISSA** | [🇬🇧 Getting Started](https://irena-40cc50.gitlab.io/getting-started-en/) / [🇩🇪 Erste Schritte](https://irena-40cc50.gitlab.io/getting-started-de/) |
| Learn GitLab workflow | [→ Interactive Slides](https://irena-40cc50.gitlab.io/guides/contributing/) |
| Contribute code | [→ Contributing Guide](https://irena-40cc50.gitlab.io/contributing/) |

---

## 📚 Documentation

**[→ Full Documentation (GitLab Pages)](https://irena-40cc50.gitlab.io/)**

| Quick Links | |
|-------------|---|
| [🚀 Getting Started 🇬🇧](https://irena-40cc50.gitlab.io/getting-started-en/) | Installation, first run, deployment |
| [🚀 Erste Schritte 🇩🇪](https://irena-40cc50.gitlab.io/getting-started-de/) | Installation, erster Start, Deployment |
| [Contributing Guide](https://irena-40cc50.gitlab.io/contributing/) | How to contribute |
| [Workflow Slides](https://irena-40cc50.gitlab.io/guides/contributing/) | Interactive 5-min intro |
| [Runner Management 🇬🇧](https://irena-40cc50.gitlab.io/runner-management-en/) | Start/Stop Runner & GCP VM |
| [Runner Verwaltung 🇩🇪](https://irena-40cc50.gitlab.io/runner-management-de/) | Runner starten/stoppen |
| [CI Guide](https://irena-40cc50.gitlab.io/ci/) | How to read CI results |
| [ADRs](https://irena-40cc50.gitlab.io/architecture/adr/) | Architecture decisions |
| [Publications](https://irena-40cc50.gitlab.io/publications/) | Research papers (SPE Europe 2026) |

---

## 🌍 Available Languages

| Language | Getting Started | Runner Management | Cheatsheet |
|----------|-----------------|-------------------|------------|
| 🇬🇧 English | [Guide](https://irena-40cc50.gitlab.io/getting-started-en/) | [Guide](https://irena-40cc50.gitlab.io/runner-management-en/) | [Cheatsheet](https://irena-40cc50.gitlab.io/guides/contributing/cheatsheet-en/) |
| 🇩🇪 Deutsch | [Anleitung](https://irena-40cc50.gitlab.io/getting-started-de/) | [Anleitung](https://irena-40cc50.gitlab.io/runner-management-de/) | [Cheatsheet](https://irena-40cc50.gitlab.io/guides/contributing/cheatsheet-de/) |
| 🇻🇳 Tiếng Việt | [Hướng dẫn](https://irena-40cc50.gitlab.io/getting-started-vi/) | [Hướng dẫn](https://irena-40cc50.gitlab.io/runner-management-vi/) | [Cheatsheet](https://irena-40cc50.gitlab.io/guides/contributing/cheatsheet-vi/) |
| 🇸🇦 العربية | [دليل](https://irena-40cc50.gitlab.io/getting-started-ar/) | [دليل](https://irena-40cc50.gitlab.io/runner-management-ar/) | [Cheatsheet](https://irena-40cc50.gitlab.io/guides/contributing/cheatsheet-ar/) |
| 🇮🇸 Íslenska | [Leiðbeiningar](https://irena-40cc50.gitlab.io/getting-started-is/) | [Leiðbeiningar](https://irena-40cc50.gitlab.io/runner-management-is/) | [Cheatsheet](https://irena-40cc50.gitlab.io/guides/contributing/cheatsheet-is/) |

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
docs/i18n/              # Internationalization templates and translations
docs/ci/                # CI philosophy and automation documentation
docs/simulators/        # Simulator adapter matrix and notes

scripts/                # Operational and CI tooling
tests/                  # Contract tests, golden CLI tests, governance checks
```

---

## Quick Start

```bash
# Clone
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git clarissa
cd clarissa

# Install
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Test
pytest

# Run
clarissa --help
```

**[→ Detailed instructions in Getting Started Guide](https://irena-40cc50.gitlab.io/getting-started-en/)**

---

## CI/CD Pipeline

| Job | Description |
|-----|-------------|
| `tests` | Run pytest |
| `pages` | Deploy documentation |
| `gcp-vm-start` | Start GCP Runner (manual) |
| `gcp-vm-stop` | Stop GCP Runner (manual) |

**[→ Full CI Guide](https://irena-40cc50.gitlab.io/ci/)**

---

*Built by BlauWeiss LLC*

---
_GitHub↔GitLab sync test: 2026-01-23T22:15Z_ ✅
