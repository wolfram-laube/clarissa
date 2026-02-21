"""Tests for CLARISSA Sim-Engine: SimulatorBackend ABC, models, registry.

Tests:
- Pydantic models: GridParams, WellConfig, SimRequest, UnifiedResult
- SimulatorBackend ABC: interface contract, mock implementation
- Backend registry: register/get/list, error handling
- PAL integration: PlatformAdapter inheritance, health, info

Issue #162 | Epic #161 | ADR-038
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Optional, Callable

from clarissa.pal import PlatformAdapter, AdapterRegistry
from clarissa.sim_engine.models import (
    GridParams, WellConfig, FluidProperties, SimRequest,
    UnifiedResult, CellData, WellData, TimestepResult, SimMetadata,
    SimStatus, WellType, Phase,
)
from clarissa.sim_engine.backends.base import SimulatorBackend


# ═══════════════════════════════════════════════════════════════════════════
# Mock Backend (for testing the ABC)
# ═══════════════════════════════════════════════════════════════════════════

class MockBackend(SimulatorBackend):
    """Mock simulator for testing. Returns synthetic results."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0-test"

    def validate(self, request: SimRequest) -> list[str]:
        errors = []
        if request.grid.total_cells > 10000:
            errors.append("Mock backend: max 10000 cells")
        if not request.wells:
            errors.append("No wells defined")
        return errors

    def run(
        self,
        request: SimRequest,
        work_dir: str,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> dict[str, Any]:
        if on_progress:
            on_progress(0)
            on_progress(50)
            on_progress(100)
        return {
            "mock_output": True,
            "cells": request.grid.total_cells,
            "timesteps": len(request.timesteps_days),
        }

    def parse_result(
        self,
        raw: dict[str, Any],
        request: SimRequest,
    ) -> UnifiedResult:
        n_cells = request.grid.total_cells
        timesteps = []
        for t in request.timesteps_days:
            timesteps.append(TimestepResult(
                time_days=t,
                cells=CellData(
                    pressure=[200.0] * n_cells,
                    saturation_oil=[0.8] * n_cells,
                    saturation_water=[0.2] * n_cells,
                ),
                wells=[
                    WellData(
                        well_name=w.name,
                        oil_rate_m3_day=100.0 if w.well_type == WellType.PRODUCER else 0.0,
                        water_rate_m3_day=50.0 if w.well_type == WellType.INJECTOR else 0.0,
                        bhp_bar=180.0,
                    )
                    for w in request.wells
                ],
            ))

        return UnifiedResult(
            job_id="mock-001",
            title=request.title,
            status=SimStatus.COMPLETED,
            request=request,
            timesteps=timesteps,
            metadata=SimMetadata(
                backend="mock",
                backend_version="1.0.0-test",
                grid_cells=n_cells,
                wall_time_seconds=0.01,
                converged=True,
            ),
            created_at=datetime.now(timezone.utc).isoformat(),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestGridParams:
    def test_defaults(self):
        g = GridParams()
        assert g.nx == 10
        assert g.total_cells == 100  # 10*10*1
        assert g.dimensions_m == (1000.0, 1000.0, 10.0)

    def test_custom(self):
        g = GridParams(nx=20, ny=20, nz=5, dx=50, dy=50, dz=5)
        assert g.total_cells == 2000
        assert g.dimensions_m == (1000.0, 1000.0, 25.0)

    def test_validation_bounds(self):
        with pytest.raises(Exception):
            GridParams(nx=0)  # ge=1

        with pytest.raises(Exception):
            GridParams(porosity=1.5)  # le=1

        with pytest.raises(Exception):
            GridParams(dx=-10)  # gt=0


class TestWellConfig:
    def test_producer(self):
        w = WellConfig(name="PROD1", well_type=WellType.PRODUCER, i=5, j=5,
                       rate_m3_day=100, phases=[Phase.OIL, Phase.WATER])
        assert w.name == "PROD1"
        assert w.well_type == WellType.PRODUCER

    def test_injector(self):
        w = WellConfig(name="INJ1", well_type=WellType.INJECTOR, i=0, j=0,
                       bhp_bar=250, phases=[Phase.WATER])
        assert w.bhp_bar == 250

    def test_k_validation(self):
        with pytest.raises(Exception):
            WellConfig(name="BAD", well_type=WellType.PRODUCER,
                       i=0, j=0, k_top=5, k_bottom=3)

    def test_name_validation(self):
        with pytest.raises(Exception):
            WellConfig(name="", well_type=WellType.PRODUCER, i=0, j=0)


class TestSimRequest:
    def _make_request(self, **kwargs):
        defaults = {
            "wells": [
                WellConfig(name="PROD1", well_type=WellType.PRODUCER, i=9, j=9),
                WellConfig(name="INJ1", well_type=WellType.INJECTOR, i=0, j=0,
                           rate_m3_day=-500),
            ],
        }
        defaults.update(kwargs)
        return SimRequest(**defaults)

    def test_defaults(self):
        req = self._make_request()
        assert req.backend == "opm"
        assert req.grid.total_cells == 100
        assert len(req.wells) == 2

    def test_no_wells_fails(self):
        with pytest.raises(Exception):
            SimRequest(wells=[])

    def test_custom_timesteps(self):
        req = self._make_request(timesteps_days=[10, 20, 30])
        assert req.timesteps_days == [10, 20, 30]

    def test_serialization_roundtrip(self):
        req = self._make_request()
        data = req.model_dump()
        req2 = SimRequest(**data)
        assert req2.grid.nx == req.grid.nx
        assert req2.wells[0].name == req.wells[0].name


class TestUnifiedResult:
    def _make_result(self):
        req = SimRequest(wells=[
            WellConfig(name="PROD1", well_type=WellType.PRODUCER, i=5, j=5),
        ])
        return UnifiedResult(
            job_id="test-001",
            title="Test Run",
            status=SimStatus.COMPLETED,
            request=req,
            timesteps=[
                TimestepResult(
                    time_days=30,
                    cells=CellData(pressure=[200.0] * 100),
                    wells=[WellData(well_name="PROD1", oil_rate_m3_day=100)],
                ),
                TimestepResult(
                    time_days=60,
                    cells=CellData(pressure=[195.0] * 100),
                    wells=[WellData(well_name="PROD1", oil_rate_m3_day=95)],
                ),
            ],
            metadata=SimMetadata(
                backend="mock",
                grid_cells=100,
                wall_time_seconds=1.5,
                converged=True,
            ),
        )

    def test_last_timestep(self):
        r = self._make_result()
        last = r.last_timestep
        assert last is not None
        assert last.time_days == 60

    def test_empty_timesteps(self):
        req = SimRequest(wells=[
            WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0),
        ])
        r = UnifiedResult(
            job_id="empty", request=req, timesteps=[],
            metadata=SimMetadata(backend="mock"),
        )
        assert r.last_timestep is None

    def test_summary(self):
        r = self._make_result()
        s = r.summary()
        assert s["job_id"] == "test-001"
        assert s["backend"] == "mock"
        assert s["timesteps"] == 2
        assert s["converged"] is True

    def test_json_serialization(self):
        r = self._make_result()
        json_str = r.model_dump_json()
        assert "test-001" in json_str
        # Roundtrip
        r2 = UnifiedResult.model_validate_json(json_str)
        assert r2.job_id == r.job_id
        assert len(r2.timesteps) == 2


# ═══════════════════════════════════════════════════════════════════════════
# SimulatorBackend ABC Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSimulatorBackend:
    def test_is_platform_adapter(self):
        """SimulatorBackend extends PlatformAdapter."""
        assert issubclass(SimulatorBackend, PlatformAdapter)

    def test_adapter_type(self):
        b = MockBackend()
        assert b.adapter_type == "simulator"

    def test_name_and_version(self):
        b = MockBackend()
        assert b.name == "mock"
        assert b.version == "1.0.0-test"

    def test_info_includes_version(self):
        b = MockBackend()
        info = b.info()
        assert info["name"] == "mock"
        assert info["adapter_type"] == "simulator"
        assert info["version"] == "1.0.0-test"
        assert info["healthy"] is True

    def test_validate_valid_request(self):
        b = MockBackend()
        req = SimRequest(wells=[
            WellConfig(name="P1", well_type=WellType.PRODUCER, i=5, j=5),
        ])
        errors = b.validate(req)
        assert errors == []

    def test_validate_too_many_cells(self):
        b = MockBackend()
        req = SimRequest(
            grid=GridParams(nx=100, ny=200, nz=1),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
        )
        errors = b.validate(req)
        assert len(errors) == 1
        assert "10000" in errors[0]

    def test_run_with_progress(self):
        b = MockBackend()
        req = SimRequest(wells=[
            WellConfig(name="P1", well_type=WellType.PRODUCER, i=5, j=5),
        ])
        progress_calls = []
        raw = b.run(req, "/tmp/test", on_progress=progress_calls.append)
        assert raw["mock_output"] is True
        assert progress_calls == [0, 50, 100]

    def test_parse_result(self):
        b = MockBackend()
        req = SimRequest(wells=[
            WellConfig(name="PROD1", well_type=WellType.PRODUCER, i=9, j=9),
            WellConfig(name="INJ1", well_type=WellType.INJECTOR, i=0, j=0,
                       rate_m3_day=-500),
        ])
        raw = b.run(req, "/tmp/test")
        result = b.parse_result(raw, req)

        assert isinstance(result, UnifiedResult)
        assert result.job_id == "mock-001"
        assert result.metadata.backend == "mock"
        assert result.metadata.converged is True
        assert len(result.timesteps) == len(req.timesteps_days)

        # Check well data
        last = result.last_timestep
        assert len(last.wells) == 2
        prod = next(w for w in last.wells if w.well_name == "PROD1")
        assert prod.oil_rate_m3_day == 100.0

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            SimulatorBackend()


# ═══════════════════════════════════════════════════════════════════════════
# Registry Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBackendRegistry:
    def test_register_and_get(self):
        from clarissa.sim_engine.backends.registry import register_backend, get_backend
        from clarissa.pal import AdapterRegistry
        # Use fresh registry
        reg = AdapterRegistry()
        mock = MockBackend()
        reg.register(mock)
        assert reg.get("simulator", "mock") is mock

    def test_list_backends(self):
        from clarissa.pal import AdapterRegistry
        reg = AdapterRegistry()
        reg.register(MockBackend())
        names = reg.list_names("simulator")
        assert "mock" in names

    def test_not_found(self):
        from clarissa.pal import AdapterRegistry
        reg = AdapterRegistry()
        with pytest.raises(KeyError, match="opm"):
            reg.get("simulator", "opm")

    def test_health_check(self):
        from clarissa.pal import AdapterRegistry
        reg = AdapterRegistry()
        reg.register(MockBackend())
        h = reg.health()
        assert h["healthy"] is True
        assert h["adapters"]["simulator"]["mock"] is True


# ═══════════════════════════════════════════════════════════════════════════
# PAL Integration Tests (in CLARISSA context)
# ═══════════════════════════════════════════════════════════════════════════

class TestPALInCLARISSA:
    def test_pal_import(self):
        from clarissa.pal import PlatformAdapter, AdapterRegistry
        assert PlatformAdapter is not None
        assert AdapterRegistry is not None

    def test_simulator_is_adapter(self):
        b = MockBackend()
        assert isinstance(b, PlatformAdapter)
        assert b.adapter_type == "simulator"

    def test_mixed_registry(self):
        """Register different adapter types in one registry."""
        from clarissa.pal import PlatformAdapter, AdapterRegistry

        class DummyEvidence(PlatformAdapter):
            adapter_type = "evidence"
            @property
            def name(self): return "dummy"

        reg = AdapterRegistry()
        reg.register(MockBackend())
        reg.register(DummyEvidence())

        assert len(reg) == 2
        assert reg.get("simulator", "mock").name == "mock"
        assert reg.get("evidence", "dummy").name == "dummy"
