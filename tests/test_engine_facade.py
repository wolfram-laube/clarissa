"""Tests for SimEngine — Thin SDK Convenience Wrapper.

Verifies that SimEngine:
1. Delegates backend management to PAL AdapterRegistry
2. Delegates run() to the backend contract
3. Delegates compare() to comparison module
4. Delegates I/O to independent modules
5. Holds no state beyond the registry reference

ADR-040 | Epic #161
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

from clarissa.pal import AdapterRegistry
from clarissa.sim_engine.engine import SimEngine
from clarissa.sim_engine.backends.base import SimulatorBackend
from clarissa.sim_engine.comparison import ComparisonReport
from clarissa.sim_engine.models import (
    CellData,
    GridParams,
    Phase,
    SimMetadata,
    SimRequest,
    SimStatus,
    TimestepResult,
    UnifiedResult,
    WellConfig,
    WellData,
    WellType,
)


# ═══════════════════════════════════════════════════════════════════════════
# Mock Backend (PAL-compliant: healthy(), not health_check())
# ═══════════════════════════════════════════════════════════════════════════


class MockBackend(SimulatorBackend):
    """PAL-compliant mock backend."""

    adapter_type = "simulator"

    def __init__(
        self,
        backend_name: str = "mock",
        pressure_base: float = 200.0,
        fail: bool = False,
        validation_errors: Optional[list[str]] = None,
    ):
        self._name = backend_name
        self._pressure_base = pressure_base
        self._fail = fail
        self._validation_errors = validation_errors or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0-mock"

    def healthy(self) -> bool:
        """PAL ABC contract — not health_check()."""
        return not self._fail

    def validate(self, request: SimRequest) -> list[str]:
        return list(self._validation_errors)

    def run(self, request, work_dir, on_progress=None) -> dict[str, Any]:
        if self._fail:
            raise RuntimeError("Simulated backend failure")
        if on_progress:
            on_progress(50)
            on_progress(100)
        return {"converged": True, "wall_time_seconds": 1.5}

    def parse_result(self, raw, request) -> UnifiedResult:
        n = request.grid.total_cells
        timesteps = []
        for t in request.timesteps_days:
            pressure = [self._pressure_base + (i / n) * 20 for i in range(n)]
            timesteps.append(TimestepResult(
                time_days=t,
                cells=CellData(
                    pressure=pressure,
                    saturation_water=[0.2] * n,
                    saturation_oil=[0.8] * n,
                ),
                wells=[WellData(well_name=w.name, bhp_bar=150)
                       for w in request.wells],
            ))
        return UnifiedResult(
            job_id=raw.get("job_id", f"{self._name}-test"),
            title=request.title,
            status=SimStatus.COMPLETED,
            request=request,
            timesteps=timesteps,
            metadata=SimMetadata(
                backend=self._name, backend_version=self.version,
                grid_cells=n, wall_time_seconds=0, converged=True,
            ),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def request_spe1() -> SimRequest:
    return SimRequest(
        grid=GridParams(nx=10, ny=10, nz=3),
        wells=[
            WellConfig(name="INJ", well_type=WellType.INJECTOR,
                       i=0, j=0, rate_m3_day=100, phases=[Phase.WATER]),
            WellConfig(name="PROD", well_type=WellType.PRODUCER,
                       i=9, j=9, bhp_bar=150, phases=[Phase.OIL]),
        ],
        timesteps_days=[30, 90, 365],
        title="SPE1 Test",
    )


@pytest.fixture
def fresh_registry() -> AdapterRegistry:
    """Fresh registry per test — no global singleton leaks."""
    return AdapterRegistry()


@pytest.fixture
def engine(fresh_registry) -> SimEngine:
    """SimEngine backed by a fresh PAL registry with two mock backends."""
    fresh_registry.register(MockBackend(backend_name="opm", pressure_base=200))
    fresh_registry.register(MockBackend(backend_name="mrst", pressure_base=202))
    return SimEngine(registry=fresh_registry)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Registry Delegation — SimEngine has NO own backend state
# ═══════════════════════════════════════════════════════════════════════════


class TestRegistryDelegation:

    def test_register_delegates_to_pal(self, fresh_registry):
        engine = SimEngine(registry=fresh_registry)
        engine.register(MockBackend(backend_name="opm"))
        # Backend is in PAL registry, not in SimEngine
        assert fresh_registry.get("simulator", "opm").name == "opm"

    def test_backends_from_registry(self, engine):
        assert "opm" in engine.backends
        assert "mrst" in engine.backends

    def test_get_backend_from_registry(self, engine):
        b = engine.get_backend("opm")
        assert b.name == "opm"

    def test_unknown_backend_raises(self, engine):
        with pytest.raises(KeyError):
            engine.get_backend("eclipse")

    def test_empty_registry(self, fresh_registry):
        engine = SimEngine(registry=fresh_registry)
        assert engine.backends == []

    def test_shared_registry(self, fresh_registry):
        """Two SimEngine instances share the same registry."""
        fresh_registry.register(MockBackend(backend_name="opm"))
        e1 = SimEngine(registry=fresh_registry)
        e2 = SimEngine(registry=fresh_registry)
        assert e1.backends == e2.backends == ["opm"]

    def test_registry_registration_visible_to_engine(self, fresh_registry):
        """Register directly on registry → visible through engine."""
        engine = SimEngine(registry=fresh_registry)
        fresh_registry.register(MockBackend(backend_name="opm"))
        assert "opm" in engine.backends


# ═══════════════════════════════════════════════════════════════════════════
# 2. Run — Delegates to backend contract
# ═══════════════════════════════════════════════════════════════════════════


class TestRun:

    def test_run_returns_unified_result(self, engine, request_spe1):
        result = engine.run(request_spe1, backend="opm")
        assert isinstance(result, UnifiedResult)
        assert result.status == SimStatus.COMPLETED

    def test_run_correct_backend(self, engine, request_spe1):
        result = engine.run(request_spe1, backend="opm")
        assert result.metadata.backend == "opm"

    def test_run_other_backend(self, engine, request_spe1):
        result = engine.run(request_spe1, backend="mrst")
        assert result.metadata.backend == "mrst"

    def test_run_uses_request_backend(self, engine, request_spe1):
        request_spe1.backend = "mrst"
        result = engine.run(request_spe1)
        assert result.metadata.backend == "mrst"

    def test_run_has_timesteps(self, engine, request_spe1):
        result = engine.run(request_spe1, backend="opm")
        assert len(result.timesteps) == 3

    def test_run_has_cell_data(self, engine, request_spe1):
        result = engine.run(request_spe1, backend="opm")
        assert len(result.timesteps[0].cells.pressure) == 300

    def test_run_progress_callback(self, engine, request_spe1):
        calls = []
        engine.run(request_spe1, backend="opm",
                    on_progress=lambda p: calls.append(p))
        assert 50 in calls and 100 in calls

    def test_run_validation_failure_raises(self, fresh_registry, request_spe1):
        fresh_registry.register(
            MockBackend(backend_name="opm", validation_errors=["Bad grid"]))
        engine = SimEngine(registry=fresh_registry)
        with pytest.raises(ValueError, match="Validation failed"):
            engine.run(request_spe1, backend="opm")

    def test_run_backend_failure_raises(self, fresh_registry, request_spe1):
        """Thin SDK re-raises — no swallowing errors."""
        fresh_registry.register(MockBackend(backend_name="opm", fail=True))
        engine = SimEngine(registry=fresh_registry)
        with pytest.raises(RuntimeError):
            engine.run(request_spe1, backend="opm")


# ═══════════════════════════════════════════════════════════════════════════
# 3. Compare — Delegates to comparison module
# ═══════════════════════════════════════════════════════════════════════════


class TestCompare:

    def test_identical_results(self, engine, request_spe1):
        a = engine.run(request_spe1, backend="opm")
        b = engine.run(request_spe1, backend="opm")
        report = engine.compare(a, b)
        assert report.match_quality == "excellent"
        assert report.overall_nrmse == 0.0

    def test_cross_backend(self, engine, request_spe1):
        a = engine.run(request_spe1, backend="opm")
        b = engine.run(request_spe1, backend="mrst")
        report = engine.compare(a, b)
        assert isinstance(report, ComparisonReport)
        assert report.is_cross_backend

    def test_labels_passed_through(self, engine, request_spe1):
        a = engine.run(request_spe1, backend="opm")
        b = engine.run(request_spe1, backend="mrst")
        report = engine.compare(a, b, "OPM Flow", "MRST Octave")
        assert report.label_a == "OPM Flow"
        assert report.label_b == "MRST Octave"

    def test_difference_detected(self, engine, request_spe1):
        """OPM mock: p=200, MRST mock: p=202 → NRMSE > 0."""
        a = engine.run(request_spe1, backend="opm")
        b = engine.run(request_spe1, backend="mrst")
        report = engine.compare(a, b)
        assert report.overall_nrmse > 0


# ═══════════════════════════════════════════════════════════════════════════
# 4. I/O Delegation
# ═══════════════════════════════════════════════════════════════════════════


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "decks"


class TestIODelegation:

    def test_parse_deck_delegates(self, engine):
        deck_path = FIXTURES_DIR / "spe1" / "SPE1CASE2.DATA"
        if not deck_path.exists():
            pytest.skip("SPE1 fixture not available")
        request = engine.parse_deck(str(deck_path))
        assert isinstance(request, SimRequest)
        assert request.grid.nx == 10

    def test_generate_deck_delegates(self, engine, request_spe1):
        deck = engine.generate_deck(request_spe1)
        assert "RUNSPEC" in deck

    def test_read_output_delegates(self, engine):
        """Verify delegation to eclipse_reader."""
        try:
            from clarissa.sim_engine.eclipse_reader import read_eclipse_output
        except ImportError:
            pytest.skip("eclipse_reader not available")

        import datetime, numpy as np
        from resdata.summary import Summary
        import resfo

        with tempfile.TemporaryDirectory() as tmp:
            case = f"{tmp}/TEST"
            # Minimal SMSPEC
            s = Summary.writer(case, datetime.datetime(2025, 1, 1), 10, 10, 3)
            s.add_variable("FPR")
            ts = s.add_t_step(1, 30.0)
            ts["FPR"] = 4800
            s.fwrite()
            # Minimal UNRST
            records = [
                ("SEQNUM  ", np.array([1], dtype=np.int32)),
                ("INTEHEAD", np.zeros(95, dtype=np.int32)),
                ("PRESSURE", np.full(300, 330.0, dtype=np.float32)),
                ("SWAT    ", np.full(300, 0.2, dtype=np.float32)),
                ("SGAS    ", np.zeros(300, dtype=np.float32)),
            ]
            resfo.write(f"{case}.UNRST", records)

            result = engine.read_output(case, unit_system="FIELD")
            assert isinstance(result, UnifiedResult)
            assert result.status == SimStatus.COMPLETED


# ═══════════════════════════════════════════════════════════════════════════
# 5. Health — Delegates to PAL Registry
# ═══════════════════════════════════════════════════════════════════════════


class TestHealth:

    def test_health_delegates_to_registry(self, engine):
        h = engine.health()
        assert "healthy" in h
        assert "adapters" in h

    def test_healthy_backends(self, engine):
        h = engine.health()
        assert h["healthy"] is True

    def test_unhealthy_backend(self, fresh_registry):
        fresh_registry.register(MockBackend(backend_name="opm", fail=True))
        engine = SimEngine(registry=fresh_registry)
        h = engine.health()
        assert h["healthy"] is False
