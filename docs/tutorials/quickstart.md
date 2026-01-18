# Quick Start Guide

Get CLARISSA tutorials running in under 5 minutes.

---

## Option A: GitPod (One-Click)

1. **Click the button:**

    [![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://gitlab.com/wolfram_laube/blauweiss_llc/irena)

2. **Wait for setup** (~2 minutes first time, then cached)

3. **Open Jupyter Lab** (opens automatically in a new tab)

4. **Navigate to** `docs/tutorials/notebooks/`

5. **Start with** `01_ECLIPSE_Fundamentals.ipynb`

!!! success "What's included"
    - PostgreSQL 15 with pgvector extension
    - OPM Flow via Docker
    - Python 3.11 with all dependencies
    - VS Code with Jupyter extension

---

## Option B: Google Colab (GPU)

Best when you need GPU power for training.

### Step 1: Open Colab

Go to [colab.research.google.com](https://colab.research.google.com)

### Step 2: Create new notebook and run setup

```python
# CLARISSA Colab Setup
import os

# Clone repository
!git clone --depth 1 https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
%cd irena/docs/tutorials

# Install dependencies
!pip install -q \
    numpy pandas matplotlib seaborn \
    sentence-transformers \
    openai anthropic langchain \
    z3-solver \
    fastapi httpx

print("✅ Setup complete!")
print("📁 Open the file browser (folder icon) to see notebooks")
```

### Step 3: Enable GPU (if needed)

1. Go to **Runtime** → **Change runtime type**
2. Select **T4 GPU** or **A100** (if available)
3. Click **Save**

### Step 4: Open notebooks

Use the file browser (📁) on the left to navigate to `notebooks/` and open any `.ipynb` file.

!!! warning "Colab Limitations"
    - No PostgreSQL → We provide `SimpleVectorStore` (SQLite-based)
    - No OPM Flow → We provide `MockOPMFlow` (synthetic results)
    - Session resets → Save work to Google Drive

---

## Option C: Local Installation

For advanced users who prefer local development.

### Prerequisites

- Python 3.10+
- Docker (for OPM Flow)
- PostgreSQL 15+ (for Knowledge Layer)

### Setup

```bash
# Clone repository
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
cd irena/docs/tutorials

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter lab
```

### PostgreSQL Setup

```bash
# Install pgvector
# Ubuntu:
sudo apt install postgresql postgresql-contrib
cd /tmp && git clone https://github.com/pgvector/pgvector.git
cd pgvector && make && sudo make install

# Create database
sudo -u postgres psql << EOF
CREATE USER clarissa WITH PASSWORD 'clarissa';
CREATE DATABASE clarissa OWNER clarissa;
\c clarissa
CREATE EXTENSION vector;
EOF
```

### OPM Flow Setup

```bash
# Pull Docker image
docker pull opmproject/opm-simulators:latest

# Test
docker run --rm opmproject/opm-simulators flow --help
```

---

## Verify Installation

Run this in any notebook to verify your environment:

```python
# Environment check
import sys
print(f"Python: {sys.version}")

# Core packages
import numpy as np
import pandas as pd
print(f"NumPy: {np.__version__}")
print(f"Pandas: {pd.__version__}")

# Check for GPU (Colab)
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
except ImportError:
    print("PyTorch: Not installed")

# Check for pgvector (GitPod/Local)
try:
    import psycopg2
    print("psycopg2: ✅")
except ImportError:
    print("psycopg2: ❌ (using SQLite fallback)")

print("\n✅ Environment ready!")
```

---

## Next Steps

1. **Complete Notebook 01** - Learn ECLIPSE deck structure
2. **Complete Notebook 02** - Run your first simulation
3. **Complete Notebook 03** - Query the knowledge base
4. **Join discussions** - Ask questions in GitLab Issues

Happy learning! 🛢️
