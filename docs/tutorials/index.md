# 📓 CLARISSA Tutorials

Interactive Jupyter notebooks that teach you how to build conversational interfaces for reservoir simulation.

---

## 🚀 Choose Your Environment

### Option A: GitPod (Recommended for Development)

Full development environment with PostgreSQL, OPM Flow, and all dependencies pre-configured.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa)

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
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa.git
cd clarissa

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scriptsctivate   # Windows

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


#### Git Workflow (Contributing Changes)

The CLARISSA repository is **bidirectionally synchronized** between GitLab and GitHub. You can work from either platform.

!!! info "Two Repositories, Fully Synced"
    | Repository | URL | Use Case |
    |------------|-----|----------|
    | **GitLab** (primary) | `gitlab.com/wolfram_laube/blauweiss_llc/clarissa` | CI/CD, MRs, main development |
    | **GitHub** (mirror) | `github.com/wolfram-laube/clarissa` | Colab notebooks, external collaboration |
    
    Both repos stay in sync automatically. Push to whichever you cloned from.

**Step 1: Clone the Repository**

```bash
# Option A: Clone from GitLab
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa.git
cd clarissa

# Option B: Clone from GitHub (for Colab users)
git clone https://github.com/wolfram-laube/clarissa.git
cd clarissa
```

**Step 2: Create a Feature Branch**

!!! warning "Never commit directly to `main`"
    Always use feature branches. Direct commits to `main` bypass code review and can cause sync conflicts.

```bash
# Create and switch to a feature branch
git checkout -b feature/my-improvement

# Make your changes...
# Edit files, run tests, etc.
```

**Step 3: Commit and Push**

```bash
# Stage and commit your changes
git add .
git commit -m "feat: add waterflood example to tutorial 03"

# Push your feature branch
git push origin feature/my-improvement
```

**Step 4: Create a Merge Request**

| If you pushed to... | Create MR/PR on... | Link |
|---------------------|-------------------|------|
| GitLab | GitLab | [Create MR](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/merge_requests/new) |
| GitHub | GitLab (preferred) or GitHub | [GitLab MR](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/merge_requests/new) |

!!! tip "GitLab for Code Review"
    Even if you work on GitHub, create the Merge Request on **GitLab** where CI/CD pipelines run. Your GitHub branch will be synced to GitLab automatically.

**Repository Sync Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bidirectional Sync                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GitLab                              GitHub                    │
│   ══════                              ══════                    │
│   wolfram_laube/                      wolfram-laube/            │
│   blauweiss_llc/clarissa                 clarissa                  │
│                                                                 │
│        │                                   │                    │
│        │◄───────── Push Mirror ───────────│                    │
│        │           (immediate)             │                    │
│        │                                   │                    │
│        │────────► GitHub Actions ─────────►│                    │
│        │           (~30 seconds)           │                    │
│        │                                   │                    │
│   ┌────┴────┐                        ┌────┴────┐               │
│   │  main   │◄──────────────────────►│  main   │               │
│   │feature/*│◄──────────────────────►│feature/*│               │
│   │  tags   │◄──────────────────────►│  tags   │               │
│   └─────────┘                        └─────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**For Colab Users (Saving Notebooks):**

When you edit a notebook in Colab and want to save changes:

1. **File → Save a copy in GitHub**
2. Select repository: `wolfram-laube/clarissa`
3. Create a **new branch** (e.g., `colab/tutorial-03-update`)
4. Add a commit message
5. Click "OK"

Your branch will automatically sync to GitLab. Then create an MR on GitLab for review.

!!! danger "Avoid Merge Conflicts"
    **Don't** edit the same file on both GitLab and GitHub simultaneously. The sync takes 30-60 seconds. If two people push conflicting changes within that window, manual conflict resolution is required.
    
    **Best Practice:** Communicate with the team before editing shared files, or work on separate feature branches.

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

### 🎮 Interactive Playgrounds

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [11 CRUD Playground](notebooks/11_CRUD_Playground.ipynb) | CLARISSA API testing | ~20 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/11_CRUD_Playground.ipynb) |
| [12 GitLab API Playground](notebooks/12_GitLab_API_Playground.ipynb) | Issues, MRs, Pipelines | ~25 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/12_GitLab_API_Playground.ipynb) |
| [13 OPM Flow Playground](notebooks/13_OPM_Flow_Playground.ipynb) | Deck files, Simulation | ~30 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/13_OPM_Flow_Playground.ipynb) |
| [14 Infrastructure Playground](notebooks/14_Infrastructure_Playground.ipynb) | Runners, Sync, Metrics | ~20 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/14_Infrastructure_Playground.ipynb) |

**No prior experience required!** These playgrounds let you explore CLARISSA interactively:

- **11 CRUD**: Test the CLARISSA conversation API
- **12 GitLab**: Manage issues, merge requests, pipelines
- **13 OPM Flow**: Create and run reservoir simulations
- **14 Infrastructure**: Monitor runners, sync status, metrics


### 🎤 Showcases

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [15 OPM Flow Showcase](notebooks/15_OPM_Flow_Showcase.ipynb) | 3D Visualization, GIF Export | ~25 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/15_OPM_Flow_Showcase.ipynb) |
| [16 Voice Input Showcase 🎤](notebooks/16_Voice_Input_Showcase.ipynb) | Speech-to-Simulation | ~30 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/16_Voice_Input_Showcase.ipynb) |

!!! tip "🎤 Voice Input - Talk to Your Simulation!"
    The **Voice Input Showcase** demonstrates CLARISSA's conversational interface:
    
    - **Speech-to-Text** with OpenAI Whisper
    - **Intent Recognition** for reservoir engineering commands  
    - **Visualization Execution** triggered by voice
    
    Try saying: *"Show me the permeability"* or *"What's the water cut?"*
    
    **More resources:**
    
    - 📖 [Voice Input Tutorial](guides/voice-input-tutorial.md) - Full guide with tips
    - 🎮 [Live Voice Demo](../demos/voice-demo.html) - Browser-based demo (works with microphone!)
    - 📐 [ADR-028: Voice Architecture](../architecture/adr/ADR-028-voice-input-architecture.md) - Technical design

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




### 🎬 Complete Showcases

| Notebook | Description | Duration | Colab |
|----------|-------------|----------|-------|
| [15 OPM Flow Showcase](notebooks/15_OPM_Flow_Showcase.ipynb) | End-to-end workflow: Install → Build → Simulate → Analyze | ~15 min | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/15_OPM_Flow_Showcase.ipynb) |

**Featured Demo:** Build a 5-spot waterflood model, run OPM Flow simulation, analyze production curves, and perform sensitivity analysis - all in one notebook!

---
