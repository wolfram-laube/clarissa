"""CLARISSA Sim-Engine — Reservoir simulation orchestration.

Provides pluggable simulator backends (OPM Flow, MRST) with unified
result format, Pydantic models, and registry pattern.

Issue #162 | Epic #161 | ADR-038
"""
from .models import (
    GridParams,
    WellConfig,
    FluidProperties,
    SimRequest,
    UnifiedResult,
    CellData,
    WellData,
    TimestepResult,
    SimMetadata,
    SimStatus,
    WellType,
    Phase,
)
from .backends import SimulatorBackend, register_backend, get_backend, list_backends

__all__ = [
    # Models
    "GridParams", "WellConfig", "FluidProperties", "SimRequest",
    "UnifiedResult", "CellData", "WellData", "TimestepResult",
    "SimMetadata", "SimStatus", "WellType", "Phase",
    # Backend system
    "SimulatorBackend", "register_backend", "get_backend", "list_backends",
]
