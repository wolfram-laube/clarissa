# 📓 CLARISSA Tutorials

Interactive Jupyter notebooks that teach you how to build conversational interfaces for reservoir simulation.

---

## 🚀 Choose Your Environment

### Option A: GitPod (Recommended for Development)

Full development environment with PostgreSQL, OPM Flow, and all dependencies pre-configured.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://gitlab.com/wolfram_laube/blauweiss_llc/irena)

### Option B: Google Colab (Best for GPU Training)

One-click access via the Colab badges in the tables below. Free GPU access (T4/A100).

!!! warning "First-Time Setup (Private Repo)"
    Since CLARISSA is a private repository, you need to connect your GitHub account to Colab once:
    
    1. Click any Colab badge below
    2. Colab will ask you to authorize GitHub access
    3. Log in with your GitHub account (`wolfram-laube` org access required)
    4. Done! Future clicks will open notebooks directly.

!!! note "Colab Limitations"
    Colab doesn't have PostgreSQL or OPM Flow installed. The notebooks use SQLite fallback for vector storage and a mock simulator for demos. For production work, use GitPod or local setup.

### Option C: Local Setup (Your Own Machine)

Run the notebooks on your laptop or workstation with full control.

#### Prerequisites

- Python 3.10+ 
- pip or conda
- Git
- (Optional) Docker for OPM Flow

#### Quick Start

```bash
# 1. Clone the repository
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
cd irena

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r docs/tutorials/requirements.txt

# 4. Launch Jupyter
cd docs/tutorials
jupyter lab
```

#### Full Local Setup (with OPM Flow)

For running actual simulations locally:

```bash
# Install OPM Flow via Docker
docker pull opmproject/opm-simulators

# Or on Ubuntu/Debian:
sudo apt-get install software-properties-common
sudo apt-add-repository ppa:opm/ppa
sudo apt-get update
sudo apt-get install mpi-default-bin libopm-simulators-bin

# Verify installation
flow --version
```

#### Dependencies Overview

The `requirements.txt` includes:

| Package | Purpose |
|---------|---------|
| `numpy`, `pandas` | Data handling |
| `matplotlib`, `seaborn` | Visualization |
| `sentence-transformers` | Embeddings for RAG |
| `openai`, `anthropic` | LLM APIs (optional) |
| `langchain` | LLM orchestration |
| `z3-solver` | Constraint engine |
| `fastapi`, `httpx` | API framework |

!!! tip "API Keys"
    For notebooks using LLM APIs, set your keys:
    ```bash
    export OPENAI_API_KEY="sk-..."
    export ANTHROPIC_API_KEY="sk-ant-..."
    ```

---

## 📚 Learning Path

### Beginner (Notebooks 01-03)

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [01 ECLIPSE Fundamentals](notebooks/01_ECLIPSE_Fundamentals.ipynb) | Deck structure, keywords, parsers | ~45 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/01_ECLIPSE_Fundamentals.ipynb) |
| [02 OPM Flow Integration](notebooks/02_OPM_Flow_Integration.ipynb) | Docker, simulation runner, results | ~30 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/02_OPM_Flow_Integration.ipynb) |
| [03 Knowledge Layer](notebooks/03_Knowledge_Layer.ipynb) | pgvector, RAG, analog database | ~45 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/03_Knowledge_Layer.ipynb) |

**After completing:** You can parse ECLIPSE decks, run simulations, and query a knowledge base.

### Intermediate (Notebooks 04-06)

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [04 LLM Conversation](notebooks/04_LLM_Conversation.ipynb) | Slot extraction, prompts, state | ~60 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/04_LLM_Conversation.ipynb) |
| [05 Constraint Engine](notebooks/05_Constraint_Engine.ipynb) | Z3, physics validation | ~45 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/05_Constraint_Engine.ipynb) |
| [06 Deck Generator](notebooks/06_Deck_Generator.ipynb) | Template engine, assembly | ~45 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/06_Deck_Generator.ipynb) |

**After completing:** You can build conversational deck generation with physics validation.

### Advanced (Notebooks 07-10)

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [07 RL Agent](notebooks/07_RL_Agent.ipynb) | PPO, reward shaping | ~90 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/07_RL_Agent.ipynb) |
| [08 RIGOR Benchmark](notebooks/08_RIGOR_Benchmark.ipynb) | Test framework, scoring | ~60 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/08_RIGOR_Benchmark.ipynb) |
| [09 Full Pipeline Demo](notebooks/09_Full_Pipeline_Demo.ipynb) | End-to-end showcase | ~30 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/09_Full_Pipeline_Demo.ipynb) |
| [10 API Reference](notebooks/10_API_Reference.ipynb) | FastAPI endpoints | ~30 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/10_API_Reference.ipynb) |

**After completing:** You understand the complete CLARISSA system and can extend it.

---

## 🛠️ Environment Comparison

| Feature | GitPod | Colab | Local |
|---------|--------|-------|-------|
| PostgreSQL + pgvector | ✅ Native | ⚠️ SQLite | ✅ Install required |
| OPM Flow | ✅ Docker | ⚠️ Mock | ✅ Docker/native |
| GPU | ❌ | ✅ T4/A100 | ⚠️ If available |
| Persistent files | ✅ Git | ⚠️ Google Drive | ✅ Local disk |
| Direct notebook links | ✅ | ✅ | ✅ |
| Setup time | ~2 min | ~1 min | ~15 min |

**Recommendation:** 

- **Development:** Use GitPod (full features, zero setup)
- **GPU Training:** Use Colab (free GPU access)
- **Offline Work:** Use local setup (full control)

---

## 📖 Prerequisites

- Basic Python knowledge
- Familiarity with Jupyter notebooks
- (Optional) Reservoir engineering fundamentals

No prior ECLIPSE or simulation experience required - we'll teach you!

---

## 🔗 Related Resources

- [SPE-221987: Envoy Reservoir Simulation Assistant](https://doi.org/10.2118/221987-MS)
- [OPM Flow Documentation](https://opm-project.org)
- [CLARISSA Architecture Overview](../architecture/README.md)
- [ADR-011: OPM Flow Integration](../architecture/adr/ADR-011-opm-flow-integration.md)

---

## ❓ Troubleshooting

### "Module not found" errors

```bash
pip install -r requirements.txt --upgrade
```

### OPM Flow not working locally

```bash
# Check if Docker is running
docker ps

# Pull latest image
docker pull opmproject/opm-simulators

# Test
docker run --rm opmproject/opm-simulators flow --help
```

### Colab session disconnects

Save your work frequently. Use Google Drive mount for persistence:

```python
from google.colab import drive
drive.mount('/content/drive')
```