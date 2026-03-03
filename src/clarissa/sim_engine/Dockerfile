# =============================================================================
# CLARISSA Sim-Engine API — Thin app layer on pre-built OPM base
# =============================================================================
# Base image (opm-base) has: Ubuntu 24.04, OPM Flow, Python, FastAPI, etc.
# This Dockerfile ONLY copies application code => fast builds (~10s)
#
# Base image: see Dockerfile.opm-base (manual/rare rebuild)
# Issue #112 | Epic #110 | ADR-038
# =============================================================================

ARG OPM_BASE_IMAGE=registry.gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa/opm-base:latest
FROM ${OPM_BASE_IMAGE}

ENV PORT=8080

WORKDIR /app

# Copy ONLY application code (the expensive stuff is in base image)
COPY src/clarissa/ /app/clarissa/

# Verify flow still works
RUN flow --version || echo "WARNING: flow binary not in PATH"

USER simuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "clarissa.sim_engine.sim_api:app", "--host", "0.0.0.0", "--port", "8080"]
