"""Sim-Engine FastAPI Service — Async reservoir simulation gateway.

Provides REST API for submitting simulation jobs, polling status,
and retrieving results. Uses the same async job pattern as the
Dialectic Engine service.

Endpoints:
    POST /sim/run           → Submit simulation job
    GET  /sim/{job_id}      → Poll status + progress
    GET  /sim/{id}/result   → Full UnifiedResult JSON
    GET  /sim/compare/{a}/{b} → Delta analysis (future)
    GET  /health            → Engine status + available backends

Issue #165 | Epic #161 | ADR-038
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from clarissa.sim_engine.models import (
    SimRequest,
    SimStatus,
    UnifiedResult,
)
from clarissa.sim_engine.backends.base import SimulatorBackend
from clarissa.sim_engine.backends.registry import get_backend, list_backends, get_registry

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Register available backends on startup."""
    try:
        from clarissa.sim_engine.backends.opm_backend import OPMBackend
        backend = OPMBackend()
        from clarissa.sim_engine.backends.registry import register_backend
        register_backend(backend)
        logger.info(f"OPM backend registered (version: {backend.version})")
    except Exception as e:
        logger.warning(f"OPM backend not available: {e}")

    backends = list_backends()
    logger.info(f"Sim-Engine started. Available backends: {backends}")
    yield


# ─── App Setup ────────────────────────────────────────────────────────────

app = FastAPI(
    title="CLARISSA Sim-Engine",
    description="Reservoir simulation gateway — OPM Flow + MRST backends",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-Memory Job Store ─────────────────────────────────────────────────

class JobState(BaseModel):
    """In-memory job tracking."""
    job_id: str
    status: SimStatus = SimStatus.PENDING
    progress: int = 0
    request: SimRequest
    result: Optional[UnifiedResult] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""


# Job store: job_id → JobState
_jobs: dict[str, JobState] = {}
_MAX_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))


# ─── API Models ──────────────────────────────────────────────────────────

class SimSubmitResponse(BaseModel):
    job_id: str
    status: SimStatus
    message: str


class SimStatusResponse(BaseModel):
    job_id: str
    status: SimStatus
    progress: int
    error: Optional[str] = None
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: str
    backends: list[str]
    active_jobs: int
    max_jobs: int
    version: str


# ─── Background Worker ───────────────────────────────────────────────────

def _run_simulation(job_id: str) -> None:
    """Background worker that runs a simulation job.

    Called via BackgroundTasks — runs in a thread pool.
    """
    job = _jobs.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        job.status = SimStatus.RUNNING
        job.updated_at = datetime.now(timezone.utc).isoformat()

        # Get backend
        backend_name = job.request.backend
        try:
            backend = get_backend(backend_name)
        except KeyError:
            raise RuntimeError(f"Backend '{backend_name}' not registered")

        # Validate
        errors = backend.validate(job.request)
        if errors:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")

        def on_progress(pct: int) -> None:
            job.progress = pct
            job.updated_at = datetime.now(timezone.utc).isoformat()

        # Run in temp directory
        with tempfile.TemporaryDirectory(prefix=f"clarissa-sim-{job_id}-") as work_dir:
            raw = backend.run(job.request, work_dir, on_progress=on_progress)
            raw["job_id"] = job_id

            # Parse result
            result = backend.parse_result(raw, job.request)
            result.job_id = job_id
            result.created_at = job.created_at

            job.result = result
            job.status = result.status
            job.progress = 100

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        job.status = SimStatus.FAILED
        job.error = str(e)

    finally:
        job.updated_at = datetime.now(timezone.utc).isoformat()


# ─── Endpoints ────────────────────────────────────────────────────────────

@app.get("/sim/list")
async def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    """List recent simulation jobs."""
    jobs = sorted(
        _jobs.values(),
        key=lambda j: j.created_at,
        reverse=True,
    )[:limit]

    return [
        {
            "job_id": j.job_id,
            "status": j.status.value,
            "progress": j.progress,
            "backend": j.request.backend,
            "grid_cells": j.request.grid.total_cells,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@app.post("/sim/run", response_model=SimSubmitResponse)
async def submit_simulation(
    request: SimRequest,
    background_tasks: BackgroundTasks,
) -> SimSubmitResponse:
    """Submit a new simulation job.

    The simulation runs asynchronously. Use GET /sim/{job_id} to poll status.
    """
    # Check capacity
    active = sum(1 for j in _jobs.values() if j.status == SimStatus.RUNNING)
    if active >= _MAX_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many active jobs ({active}/{_MAX_JOBS}). Try again later.",
        )

    # Check backend exists
    available = list_backends()
    if request.backend not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{request.backend}' not available. Available: {available}",
        )

    # Create job
    job_id = f"sim-{uuid.uuid4().hex[:12]}"
    job = JobState(job_id=job_id, request=request)
    _jobs[job_id] = job

    # Queue background work
    background_tasks.add_task(_run_simulation, job_id)

    return SimSubmitResponse(
        job_id=job_id,
        status=SimStatus.PENDING,
        message=f"Simulation queued on '{request.backend}' backend",
    )


@app.get("/sim/{job_id}", response_model=SimStatusResponse)
async def get_status(job_id: str) -> SimStatusResponse:
    """Poll simulation job status and progress."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return SimStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@app.get("/sim/{job_id}/result")
async def get_result(job_id: str) -> dict[str, Any]:
    """Get full simulation result.

    Returns the UnifiedResult as JSON. Only available when status=completed.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if job.status == SimStatus.PENDING or job.status == SimStatus.RUNNING:
        raise HTTPException(
            status_code=202,
            detail=f"Job still {job.status.value} ({job.progress}%)",
        )

    if job.status == SimStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {job.error}",
        )

    if not job.result:
        raise HTTPException(status_code=500, detail="Result not available")

    return job.result.model_dump()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Engine health check — shows available backends and capacity."""
    backends = list_backends()
    active = sum(1 for j in _jobs.values() if j.status == SimStatus.RUNNING)

    return HealthResponse(
        status="healthy" if backends else "degraded",
        backends=backends,
        active_jobs=active,
        max_jobs=_MAX_JOBS,
        version="0.1.0",
    )



# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
