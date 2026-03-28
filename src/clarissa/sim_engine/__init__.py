"""CLARISSA Sim-Engine — Reservoir simulation orchestration.

Architecture (ADR-040, ICE v2.1):
    Independent modules connected through PAL Registry + Pydantic models.
    No god class — each module has one responsibility.

Primary API (use directly in services):
    from clarissa.sim_engine.backends.registry import get_backend
    from clarissa.sim_engine.comparison import compare
    from clarissa.sim_engine.deck_parser import parse_deck_file
    from clarissa.sim_engine.eclipse_reader import read_eclipse_output
    from clarissa.sim_engine.deck_generator import generate_deck

Convenience SDK (for notebooks/REPL):
    from clarissa.sim_engine import SimEngine
    engine = SimEngine()
    result = engine.run(request, backend="opm")

Epic #161 | ADR-040
"""
from .engine import SimEngine
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
from .deck_generator import generate_deck, write_deck
from .comparison import compare, ComparisonReport

__all__ = [
    # Convenience SDK
    "SimEngine",
    # Models (the contract surface)
    "GridParams", "WellConfig", "FluidProperties", "SimRequest",
    "UnifiedResult", "CellData", "WellData", "TimestepResult",
    "SimMetadata", "SimStatus", "WellType", "Phase",
    # Backend system (PAL)
    "SimulatorBackend", "register_backend", "get_backend", "list_backends",
    # Independent modules
    "generate_deck", "write_deck", "compare", "ComparisonReport",
]
