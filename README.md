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
| **Install & run CLARISSA** | [🇬🇧 Getting Started](https://clarissa-40cc50.gitlab.io/getting-started-en/) / [🇩🇪 Erste Schritte](https://clarissa-40cc50.gitlab.io/getting-started-de/) |
| Learn GitLab workflow | [→ Interactive Slides](https://clarissa-40cc50.gitlab.io/guides/contributing/) |
| Contribute code | [→ Contributing Guide](https://clarissa-40cc50.gitlab.io/contributing/) |

---

## 📚 Documentation

**[→ Full Documentation (GitLab Pages)](https://clarissa-40cc50.gitlab.io/)**

| Quick Links | |
|-------------|---|
| [🚀 Getting Started 🇬🇧](https://clarissa-40cc50.gitlab.io/getting-started-en/) | Installation, first run, deployment |
| [🚀 Erste Schritte 🇩🇪](https://clarissa-40cc50.gitlab.io/getting-started-de/) | Installation, erster Start, Deployment |
| [Contributing Guide](https://clarissa-40cc50.gitlab.io/contributing/) | How to contribute |
| [Workflow Slides](https://clarissa-40cc50.gitlab.io/guides/contributing/) | Interactive 5-min intro |
| [Runner Management 🇬🇧](https://clarissa-40cc50.gitlab.io/runner-management-en/) | Start/Stop Runner & GCP VM |
| [Runner Verwaltung 🇩🇪](https://clarissa-40cc50.gitlab.io/runner-management-de/) | Runner starten/stoppen |
| [CI Guide](https://clarissa-40cc50.gitlab.io/ci/) | How to read CI results |
| [ADRs](https://clarissa-40cc50.gitlab.io/architecture/adr/) | Architecture decisions |
| [🎮 Demos](https://clarissa-40cc50.gitlab.io/demos/voice-demo.html) | Voice Input & Screen Recorder |
| [Publications](https://clarissa-40cc50.gitlab.io/publications/) | Research papers (SPE Europe 2026) |
---

## 🎤 Voice Input (NEW!)

Control CLARISSA with your voice! Speak natural language commands to visualize reservoir data.

| Try it now | |
|------------|---|
| [🎮 **Live Demo**](https://clarissa-40cc50.gitlab.io/demos/voice-demo.html) | Browser-based, no install needed |
| [📖 Tutorial](https://clarissa-40cc50.gitlab.io/tutorials/voice-input/) | Full documentation |
| [📓 Colab Notebook](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/16_Voice_Input_Showcase.ipynb) | Interactive playground |

**Example commands:**
- *"Show me the permeability distribution"* → 3D visualization
- *"Show layer 3"* → Cross-section with well markers
- *"What is the water cut?"* → Query simulation results



---

## 🌍 Available Languages

| Language | Getting Started | Runner Management | Cheatsheet |
|----------|-----------------|-------------------|------------|
| 🇬🇧 English | [Guide](https://clarissa-40cc50.gitlab.io/getting-started-en/) | [Guide](https://clarissa-40cc50.gitlab.io/runner-management-en/) | [Cheatsheet](https://clarissa-40cc50.gitlab.io/guides/contributing/cheatsheet-en/) |
| 🇩🇪 Deutsch | [Anleitung](https://clarissa-40cc50.gitlab.io/getting-started-de/) | [Anleitung](https://clarissa-40cc50.gitlab.io/runner-management-de/) | [Cheatsheet](https://clarissa-40cc50.gitlab.io/guides/contributing/cheatsheet-de/) |
| 🇻🇳 Tiếng Việt | [Hướng dẫn](https://clarissa-40cc50.gitlab.io/getting-started-vi/) | [Hướng dẫn](https://clarissa-40cc50.gitlab.io/runner-management-vi/) | [Cheatsheet](https://clarissa-40cc50.gitlab.io/guides/contributing/cheatsheet-vi/) |
| 🇸🇦 العربية | [دليل](https://clarissa-40cc50.gitlab.io/getting-started-ar/) | [دليل](https://clarissa-40cc50.gitlab.io/runner-management-ar/) | [Cheatsheet](https://clarissa-40cc50.gitlab.io/guides/contributing/cheatsheet-ar/) |
| 🇮🇸 Íslenska | [Leiðbeiningar](https://clarissa-40cc50.gitlab.io/getting-started-is/) | [Leiðbeiningar](https://clarissa-40cc50.gitlab.io/runner-management-is/) | [Cheatsheet](https://clarissa-40cc50.gitlab.io/guides/contributing/cheatsheet-is/) |

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
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa.git clarissa
cd clarissa

# Install
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Test
pytest

# Run
clarissa --help
```

**[→ Detailed instructions in Getting Started Guide](https://clarissa-40cc50.gitlab.io/getting-started-en/)**

---

## CI/CD Pipeline

| Job | Description |
|-----|-------------|
| `tests` | Run pytest |
| `pages` | Deploy documentation |
| `gcp-vm-start` | Start GCP Runner (manual) |
| `gcp-vm-stop` | Stop GCP Runner (manual) |

**[→ Full CI Guide](https://clarissa-40cc50.gitlab.io/ci/)**

---

*Built by BlauWeiss LLC*

## 🎬 Recording Demo Videos

Create demo recordings with our cross-platform tools:

```bash
# Setup (one time)
./tools/recording/setup.sh

# Record with camera PiP
record-pip.sh start 60
```

**Browser alternative:** [Screen Recorder + PiP](https://clarissa-40cc50.gitlab.io/demos/screen-recorder-pip.html)

See [tools/recording/](tools/recording/) for full documentation.
