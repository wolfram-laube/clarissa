# 📓 CLARISSA Tutorials

Interactive Jupyter notebooks that teach you how to build conversational interfaces for reservoir simulation.

---

## 🚀 Quick Start

### Option A: GitPod (Recommended)

Full development environment with PostgreSQL, OPM Flow, and all dependencies.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://gitlab.com/wolfram_laube/blauweiss_llc/irena)

### Option B: Google Colab (GPU Training)

Best for RL agent training and embedding generation.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com)

```python
# Run this in your first Colab cell:
!git clone --depth 1 https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
%cd irena/docs/tutorials
!pip install -q numpy pandas matplotlib sentence-transformers langchain z3-solver
```

---

## 📚 Learning Path

### Beginner (Notebooks 01-03)

| Notebook | Description | Duration |
|----------|-------------|----------|
| [01 ECLIPSE Fundamentals](notebooks/01_ECLIPSE_Fundamentals.ipynb) | Deck structure, keywords, parsers | ~45 min |
| [02 OPM Flow Integration](notebooks/02_OPM_Flow_Integration.ipynb) | Docker, simulation runner, results | ~30 min |
| [03 Knowledge Layer](notebooks/03_Knowledge_Layer.ipynb) | pgvector, RAG, analog database | ~45 min |

**After completing:** You can parse ECLIPSE decks, run simulations, and query a knowledge base.

### Intermediate (Notebooks 04-06)

| Notebook | Description | Duration |
|----------|-------------|----------|
| [04 LLM Conversation](notebooks/04_LLM_Conversation.ipynb) | Slot extraction, prompts, state | ~60 min |
| [05 Constraint Engine](notebooks/05_Constraint_Engine.ipynb) | Z3, physics validation | ~45 min |
| [06 Deck Generator](notebooks/06_Deck_Generator.ipynb) | Template engine, assembly | ~45 min |

**After completing:** You can build conversational deck generation with physics validation.

### Advanced (Notebooks 07-10)

| Notebook | Description | Duration |
|----------|-------------|----------|
| [07 RL Agent](notebooks/07_RL_Agent.ipynb) | PPO, reward shaping | ~90 min |
| [08 RIGOR Benchmark](notebooks/08_RIGOR_Benchmark.ipynb) | Test framework, scoring | ~60 min |
| [09 Full Pipeline Demo](notebooks/09_Full_Pipeline_Demo.ipynb) | End-to-end showcase | ~30 min |
| [10 API Reference](notebooks/10_API_Reference.ipynb) | FastAPI endpoints | ~30 min |

**After completing:** You understand the complete CLARISSA system and can extend it.

---

## 🛠️ Environment Comparison

| Feature | GitPod | Colab |
|---------|--------|-------|
| PostgreSQL + pgvector | ✅ Native | ⚠️ SQLite fallback |
| OPM Flow | ✅ Docker | ⚠️ Mock simulator |
| GPU | ❌ | ✅ T4/A100 |
| Persistent files | ✅ Git | ⚠️ Google Drive |
| Full pipeline | ✅ | ⚠️ Limited |

**Recommendation:** Use GitPod for development, Colab for GPU training.

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
