# ============================================================
# CLARISSA GitPod Docker Image
# Pre-configured environment for reservoir simulation tutorials
# ============================================================

FROM gitpod/workspace-full:latest

USER root

# ============================================================
# 1. PostgreSQL + pgvector
# ============================================================
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    postgresql-server-dev-all \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector extension
RUN cd /tmp \
    && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install \
    && cd .. \
    && rm -rf pgvector

# Configure PostgreSQL for local connections
RUN echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/*/main/pg_hba.conf \
    && echo "listen_addresses='*'" >> /etc/postgresql/*/main/postgresql.conf

# ============================================================
# 2. OPM Flow Dependencies (for native builds, optional)
# ============================================================
# We primarily use Docker for OPM Flow, but install headers for Python bindings
RUN apt-get update && apt-get install -y \
    libboost-all-dev \
    libopm-common-dev \
    && rm -rf /var/lib/apt/lists/* \
    || echo "OPM dev packages not available - using Docker instead"

# ============================================================
# 3. System utilities
# ============================================================
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

USER gitpod

# ============================================================
# 4. Python Environment
# ============================================================
RUN pip install --upgrade pip

# Core scientific stack
RUN pip install \
    numpy \
    pandas \
    scipy \
    matplotlib \
    seaborn

# Jupyter ecosystem
RUN pip install \
    jupyterlab \
    ipywidgets \
    jupyter-dash

# Database & embeddings
RUN pip install \
    psycopg2-binary \
    asyncpg \
    pgvector \
    sentence-transformers

# LLM & AI
RUN pip install \
    openai \
    anthropic \
    langchain \
    langchain-community

# Web framework (for API notebooks)
RUN pip install \
    fastapi \
    uvicorn \
    httpx

# Reservoir simulation utilities
RUN pip install \
    resdata \
    ecl-data-io \
    || echo "⚠️ Reservoir packages optional - some may not be available"

# Documentation & diagrams
RUN pip install \
    mkdocs \
    mkdocs-material \
    mermaid-py

# ============================================================
# 5. Jupyter Extensions
# ============================================================
RUN pip install \
    jupyterlab-git \
    jupyterlab-mermaid

# Enable Mermaid in Jupyter
RUN jupyter labextension install @jupyterlab/toc || true

# ============================================================
# Environment variables
# ============================================================
ENV DATABASE_URL="postgresql://clarissa:clarissa@localhost:5432/clarissa"
ENV JUPYTER_ENABLE_LAB=yes

# Done!
