"""Sim-Engine Domain Models.

Pydantic models for reservoir simulation parameters, requests, and results.
These define the contract between frontends, backends, and the LLM Bridge.

Issue #162 | Epic #161 | ADR-038
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ─────────────────────────────────────────────────────────────────

class WellType(str, Enum):
    INJECTOR = "injector"
    PRODUCER = "producer"


class Phase(str, Enum):
    OIL = "oil"
    WATER = "water"
    GAS = "gas"


class SimStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Input Models ──────────────────────────────────────────────────────────

class GridParams(BaseModel):
    """Reservoir grid parameters.

    Defines the spatial discretization and rock properties.
    All units SI unless noted.
    """
    nx: int = Field(10, ge=1, le=200, description="Grid cells in X direction")
    ny: int = Field(10, ge=1, le=200, description="Grid cells in Y direction")
    nz: int = Field(1, ge=1, le=100, description="Grid cells in Z direction")

    dx: float = Field(100.0, gt=0, description="Cell size X [m]")
    dy: float = Field(100.0, gt=0, description="Cell size Y [m]")
    dz: float = Field(10.0, gt=0, description="Cell size Z [m]")

    depth_top: float = Field(2000.0, gt=0, description="Top of reservoir [m TVD]")

    porosity: float = Field(0.2, gt=0, le=1, description="Porosity [fraction]")
    permeability_x: float = Field(100.0, gt=0, description="Permeability X [mD]")
    permeability_y: float = Field(100.0, gt=0, description="Permeability Y [mD]")
    permeability_z: float = Field(10.0, gt=0, description="Permeability Z [mD]")

    @property
    def total_cells(self) -> int:
        return self.nx * self.ny * self.nz

    @property
    def dimensions_m(self) -> tuple[float, float, float]:
        """Physical dimensions in meters."""
        return (self.nx * self.dx, self.ny * self.dy, self.nz * self.dz)


class WellConfig(BaseModel):
    """Well placement and operating conditions."""
    name: str = Field(..., min_length=1, max_length=50, description="Well name")
    well_type: WellType = Field(..., description="Injector or producer")
    i: int = Field(..., ge=0, description="Grid index I (0-based)")
    j: int = Field(..., ge=0, description="Grid index J (0-based)")
    k_top: int = Field(0, ge=0, description="Top perforation layer (0-based)")
    k_bottom: int = Field(0, ge=0, description="Bottom perforation layer (0-based)")

    # Operating conditions (one of these should be set)
    rate_m3_day: Optional[float] = Field(None, description="Flow rate [m³/day]")
    bhp_bar: Optional[float] = Field(None, gt=0, description="Bottom-hole pressure [bar]")

    phases: list[Phase] = Field(default=[Phase.WATER], description="Fluid phases")

    @field_validator("k_bottom", mode="after")
    @classmethod
    def k_bottom_gte_top(cls, v, info):
        if "k_top" in info.data and v < info.data["k_top"]:
            raise ValueError("k_bottom must be >= k_top")
        return v


class FluidProperties(BaseModel):
    """Simplified fluid PVT properties."""
    oil_density_kg_m3: float = Field(800.0, gt=0, description="Oil density [kg/m³]")
    water_density_kg_m3: float = Field(1000.0, gt=0, description="Water density [kg/m³]")
    oil_viscosity_cp: float = Field(1.0, gt=0, description="Oil viscosity [cP]")
    water_viscosity_cp: float = Field(0.5, gt=0, description="Water viscosity [cP]")
    initial_pressure_bar: float = Field(200.0, gt=0, description="Initial reservoir pressure [bar]")
    bubble_point_bar: float = Field(100.0, gt=0, description="Bubble point pressure [bar]")


class SimRequest(BaseModel):
    """Complete simulation request.

    This is what the frontend/API sends to trigger a simulation run.
    """
    grid: GridParams = Field(default_factory=GridParams)
    wells: list[WellConfig] = Field(default_factory=list)
    fluid: FluidProperties = Field(default_factory=FluidProperties)
    backend: str = Field("opm", description="Simulator backend name")
    timesteps_days: list[float] = Field(
        default=[30, 60, 90, 180, 365],
        description="Report timesteps [days from start]",
    )
    title: str = Field("CLARISSA Simulation", description="Run title")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("wells")
    @classmethod
    def at_least_one_well(cls, v):
        if not v:
            raise ValueError("At least one well is required")
        return v


# ─── Output Models ─────────────────────────────────────────────────────────

class CellData(BaseModel):
    """Per-cell simulation results at a single timestep."""
    pressure: list[float] = Field(default_factory=list, description="Pressure per cell [bar]")
    saturation_oil: list[float] = Field(default_factory=list, description="Oil saturation per cell")
    saturation_water: list[float] = Field(default_factory=list, description="Water saturation per cell")
    saturation_gas: list[float] = Field(default_factory=list, description="Gas saturation per cell")


class WellData(BaseModel):
    """Per-well production/injection data at a single timestep."""
    well_name: str
    oil_rate_m3_day: float = 0.0
    water_rate_m3_day: float = 0.0
    gas_rate_m3_day: float = 0.0
    bhp_bar: float = 0.0
    cumulative_oil_m3: float = 0.0
    cumulative_water_m3: float = 0.0


class TimestepResult(BaseModel):
    """Simulation results at a single timestep."""
    time_days: float
    cells: CellData = Field(default_factory=CellData)
    wells: list[WellData] = Field(default_factory=list)


class SimMetadata(BaseModel):
    """Metadata about a simulation run."""
    backend: str = Field(..., description="Backend that produced this result")
    backend_version: str = Field("", description="Backend version string")
    grid_cells: int = Field(0, description="Total grid cells")
    wall_time_seconds: float = Field(0.0, description="Wall clock time")
    solver_iterations: int = Field(0, description="Total solver iterations")
    converged: bool = Field(True, description="Did the simulation converge?")
    warnings: list[str] = Field(default_factory=list)
    raw_output_path: Optional[str] = Field(None, description="Path to raw simulator output")


class UnifiedResult(BaseModel):
    """Unified simulation result — the contract between backends and consumers.

    This is what every SimulatorBackend.parse_result() must produce.
    The LLM Bridge's SimResultProvider formats this as evidence text.
    The frontend renders this as 3D visualization.
    """
    job_id: str = Field(..., description="Unique simulation job ID")
    title: str = Field("", description="Run title")
    status: SimStatus = Field(SimStatus.COMPLETED)
    request: SimRequest
    timesteps: list[TimestepResult] = Field(default_factory=list)
    metadata: SimMetadata
    created_at: str = Field(default="", description="ISO 8601 timestamp")

    @property
    def last_timestep(self) -> Optional[TimestepResult]:
        """Get the final timestep result."""
        return self.timesteps[-1] if self.timesteps else None

    def summary(self) -> dict[str, Any]:
        """Quick summary for logging and health checks."""
        last = self.last_timestep
        return {
            "job_id": self.job_id,
            "backend": self.metadata.backend,
            "status": self.status.value,
            "grid_cells": self.metadata.grid_cells,
            "timesteps": len(self.timesteps),
            "wall_time_s": self.metadata.wall_time_seconds,
            "converged": self.metadata.converged,
            "final_time_days": last.time_days if last else 0,
        }
