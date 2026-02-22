# =============================================================================
# CLARISSA Sim-Engine Docker Image
# Ubuntu 24.04 + OPM Flow + Python FastAPI
# Issue #165 | Epic #161 | ADR-038
# =============================================================================

# --- Stage 1: Builder ---
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install OPM PPA + dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:opm/ppa \
    && apt-get update \
    && apt-get install -y \
        libopm-simulators-bin \
        python3-pip \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --break-system-packages --no-cache-dir \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    pydantic==2.10.* \
    opm==2025.10 \
    numpy \
    httpx

# --- Stage 2: Runtime ---
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:opm/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libopm-simulators-bin \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/dist-packages /usr/local/lib/python3.12/dist-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Create app user
RUN useradd -m -s /bin/bash simuser
WORKDIR /app

# Copy application code
COPY src/clarissa/ /app/clarissa/

# Verify flow is available
RUN flow --version || echo "WARNING: flow binary not in PATH"

USER simuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

CMD ["uvicorn", "clarissa.sim_engine.sim_api:app", "--host", "0.0.0.0", "--port", "8080"]
