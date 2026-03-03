"""Sim-Engine FastAPI Service — Async reservoir simulation gateway.

Provides REST API for submitting simulation jobs, polling status,
and retrieving results. Uses the same async job pattern as the
Dialectic Engine service.

Endpoints:
    POST /sim/run           → Submit simulation job (JSON SimRequest)
    POST /sim/upload        → Upload .DATA file → parse → simulate
    GET  /sim/{job_id}      → Poll status + progress
    GET  /sim/{id}/result   → Full UnifiedResult JSON
    GET  /sim/compare/{a}/{b} → Delta analysis (future)
    GET  /health            → Engine status + available backends

Issue #165, #111 | Epic #110, #161 | ADR-038, ADR-040
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

from fastapi import FastAPI, File, HTTPException, BackgroundTasks, Query, UploadFile
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
    from clarissa.sim_engine.backends.registry import register_backend

    # OPM Flow
    try:
        from clarissa.sim_engine.backends.opm_backend import OPMBackend
        backend = OPMBackend()
        if backend.health_check():
            register_backend(backend)
            logger.info(f"OPM backend registered (version: {backend.version})")
        else:
            logger.warning("OPM backend: flow binary not found — skipped")
    except Exception as e:
        logger.warning(f"OPM backend not available: {e}")

    # MRST (Octave)
    try:
        from clarissa.sim_engine.backends.mrst_backend import MRSTBackend
        mrst = MRSTBackend()
        if mrst.health_check():
            register_backend(mrst)
            logger.info(f"MRST backend registered (version: {mrst.version})")
        else:
            logger.warning("MRST backend: octave not found — skipped")
    except Exception as e:
        logger.warning(f"MRST backend not available: {e}")

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
    logs: Optional[dict[str, Any]] = None  # raw stdout/stderr/errors from backend
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


class UploadResponse(BaseModel):
    job_id: str
    status: SimStatus
    message: str
    parsed_grid: dict[str, Any] = {}


# Upload size limit (bytes)
_MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024


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

            # Store raw logs for debugging
            job.logs = {
                "stdout": raw.get("stdout", "")[-3000:],
                "stderr": raw.get("stderr", "")[-3000:],
                "errors": raw.get("errors", []),
                "exit_code": raw.get("exit_code"),
                "output_files": list(raw.get("output_files", {}).keys()),
                "wall_time_seconds": raw.get("wall_time_seconds", 0),
            }

            # Surface error details if simulation failed
            if result.status == SimStatus.FAILED:
                error_parts = []
                if raw.get("errors"):
                    error_parts.extend(raw["errors"][:5])
                if raw.get("stderr"):
                    error_parts.append(raw["stderr"][-500:])
                job.error = "; ".join(error_parts) if error_parts else "Simulation failed (no output)"

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


@app.post("/sim/upload", response_model=UploadResponse)
async def upload_deck(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Eclipse .DATA deck file"),
    simulator: str = Query("opm", description="Backend: opm, mrst, or both"),
) -> UploadResponse:
    """Upload an Eclipse .DATA file and run simulation.

    Parses the deck, converts to SimRequest, and queues a simulation job.
    Use GET /sim/{job_id} to poll status.

    Issue #111 | Epic #110
    """
    # Validate filename
    if file.filename and not file.filename.upper().endswith(".DATA"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected .DATA file, got '{file.filename}'",
        )

    # Read content with size limit
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes). Max: {_MAX_UPLOAD_BYTES} bytes.",
        )

    if not content.strip():
        raise HTTPException(status_code=400, detail="Empty file")

    # Decode
    try:
        deck_text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            deck_text = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Cannot decode file (expected UTF-8 or Latin-1)")

    # Basic validation: must contain RUNSPEC
    if "RUNSPEC" not in deck_text.upper():
        raise HTTPException(
            status_code=400,
            detail="Invalid deck: RUNSPEC section not found",
        )

    # Parse deck → SimRequest
    try:
        from clarissa.sim_engine.deck_parser import parse_deck, deck_to_sim_request

        parsed = parse_deck(deck_text)
        sim_request = deck_to_sim_request(parsed)
        sim_request.backend = simulator
        sim_request.metadata["source"] = "upload"
        sim_request.metadata["filename"] = file.filename or "unknown.DATA"
        sim_request.metadata["_raw_deck"] = deck_text  # Preserve original for direct execution
    except Exception as e:
        logger.error(f"Deck parse failed: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Deck parsing failed: {str(e)[:200]}",
        )

    # Check capacity
    active = sum(1 for j in _jobs.values() if j.status == SimStatus.RUNNING)
    if active >= _MAX_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many active jobs ({active}/{_MAX_JOBS}). Try again later.",
        )

    # Check backend
    available = list_backends()
    if simulator not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{simulator}' not available. Available: {available}",
        )

    # Create job
    job_id = f"sim-{uuid.uuid4().hex[:12]}"
    job = JobState(job_id=job_id, request=sim_request)
    _jobs[job_id] = job

    # Queue background work
    background_tasks.add_task(_run_simulation, job_id)

    grid_info = {
        "nx": sim_request.grid.nx,
        "ny": sim_request.grid.ny,
        "nz": sim_request.grid.nz,
        "total_cells": sim_request.grid.total_cells,
        "wells": len(sim_request.wells),
        "title": sim_request.title,
    }

    logger.info(
        f"Upload: {file.filename} → job {job_id} "
        f"({grid_info['nx']}×{grid_info['ny']}×{grid_info['nz']}, "
        f"{grid_info['wells']} wells, backend={simulator})"
    )

    return UploadResponse(
        job_id=job_id,
        status=SimStatus.PENDING,
        message=(
            f"Deck '{file.filename}' parsed: "
            f"{grid_info['nx']}×{grid_info['ny']}×{grid_info['nz']} grid, "
            f"{grid_info['wells']} wells. Simulation queued on '{simulator}'."
        ),
        parsed_grid=grid_info,
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
        detail = f"Simulation failed: {job.error}"
        if job.logs:
            detail += f" | exit_code={job.logs.get('exit_code')} | errors={job.logs.get('errors', [])}"
        raise HTTPException(status_code=500, detail=detail)

    if not job.result:
        raise HTTPException(status_code=500, detail="Result not available")

    return job.result.model_dump()



@app.get("/sim/{job_id}/logs")
async def get_logs(job_id: str) -> dict[str, Any]:
    """Get raw simulation logs for debugging.

    Returns stdout, stderr, errors, exit code from OPM Flow.
    Available regardless of job status.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "error": job.error,
        "logs": job.logs or {"message": "No logs yet (job still running or logs not captured)"},
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Engine health check — shows available backends and capacity."""
    backends = list_backends()
    active = sum(1 for j in _jobs.values() if j.status == SimStatus.RUNNING)

    # Get backend versions
    backend_versions = {}
    for b in backends:
        try:
            be = get_backend(b)
            backend_versions[b] = be.version
        except Exception:
            backend_versions[b] = "unknown"

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
