# =============================================================================
# CLARISSA Sim-Engine API — Thin app layer on pre-built sim-base
# =============================================================================
# Base image (sim-base) has: Ubuntu 24.04, OPM Flow, Octave, MRST, Python
# This Dockerfile ONLY copies application code => fast builds (~10s)
#
# Base image: see Dockerfile.sim-base (manual/rare rebuild)
# Issue #117 | Epic #110 | ADR-038
# =============================================================================

ARG SIM_BASE_IMAGE=registry.gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa/sim-base:latest
FROM ${SIM_BASE_IMAGE}

ENV PORT=8080

# ── MPI/ORTE fix for Cloud Run (gVisor sandbox) ──────────────────────────
ENV OMPI_MCA_orte_launch_agent=/bin/true
ENV OMPI_MCA_btl=self
ENV OMPI_MCA_btl_vader_single_copy_mechanism=none
ENV OMPI_MCA_oob=tcp
ENV OMPI_MCA_oob_tcp_if_include=lo
ENV OMPI_MCA_orte_tmpdir_base=/tmp
ENV OMPI_MCA_shmem_posix_posix_shmdir=/tmp
ENV PMIX_MCA_gds=hash
ENV PMIX_MCA_ptl=tcp
ENV OMPI_MCA_rmaps_base_oversubscribe=1
ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# ── MRST writable dirs (mrstSettings needs to create config on first run) ─
ENV HOME=/home/simuser
RUN mkdir -p /home/simuser/.mrst /home/simuser/.config/octave     && chown -R simuser:simuser /home/simuser

WORKDIR /app

# Copy ONLY application code (the expensive stuff is in base image)
COPY src/clarissa/ /app/clarissa/

# Verify both backends still work
RUN flow --version || echo "WARNING: flow binary not in PATH"
RUN octave --no-gui --version | head -1 || echo "WARNING: octave not in PATH"

USER simuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "clarissa.sim_engine.sim_api:app", "--host", "0.0.0.0", "--port", "8080"]
