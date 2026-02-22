"""Tests for CLARISSA Sim-Engine Phase A: Deck Generator, OPM Backend, API.

Test categories:
1. Deck Generator (#164): generate valid Eclipse decks from SimRequest
2. OPM Backend (#163): validate, run, parse (mocked + reference data)
3. Sim API (#165): FastAPI endpoints, job lifecycle
4. SPE1 Reference: parse OPM reference output, validate known values
5. Integration: end-to-end with mock backend

Issue #163, #164, #165 | Epic #161 | ADR-038
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional
from unittest.mock import MagicMock, patch

import pytest

from clarissa.sim_engine.models import (
    CellData,
    FluidProperties,
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
from clarissa.sim_engine.deck_generator import (
    generate_deck,
    write_deck,
    _m_to_ft,
    _bar_to_psi,
    _m3d_to_stbd,
)
from clarissa.sim_engine.backends.opm_backend import OPMBackend


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def simple_request() -> SimRequest:
    """Simple two-well simulation request."""
    return SimRequest(
        grid=GridParams(nx=10, ny=10, nz=3, dx=100, dy=100, dz=10),
        wells=[
            WellConfig(
                name="PROD",
                well_type=WellType.PRODUCER,
                i=9, j=9,
                k_top=0, k_bottom=2,
                bhp_bar=70,
            ),
            WellConfig(
                name="INJ",
                well_type=WellType.INJECTOR,
                i=0, j=0,
                k_top=0, k_bottom=2,
                rate_m3_day=500,
                phases=[Phase.WATER],
            ),
        ],
        timesteps_days=[30, 60, 90, 180, 365],
        title="Test Simulation",
    )


@pytest.fixture
def spe1_ref_dir() -> Optional[str]:
    """Path to SPE1 reference data (if available)."""
    candidates = [
        "/home/claude/opm-tests/spe1/opm-simulation-reference/flow",
        os.path.expanduser("~/opm-tests/spe1/opm-simulation-reference/flow"),
        "opm-tests/spe1/opm-simulation-reference/flow",
    ]
    for path in candidates:
        if os.path.exists(os.path.join(path, "SPE1CASE1.UNRST")):
            return path
    return None


@pytest.fixture
def opm_backend() -> OPMBackend:
    """OPM backend instance."""
    return OPMBackend(timeout_seconds=60)


# ═══════════════════════════════════════════════════════════════════════════
# Unit Conversion Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestUnitConversions:
    def test_m_to_ft(self):
        assert abs(_m_to_ft(1.0) - 3.28084) < 0.001
        assert abs(_m_to_ft(100.0) - 328.084) < 0.01

    def test_bar_to_psi(self):
        assert abs(_bar_to_psi(1.0) - 14.5038) < 0.001
        assert abs(_bar_to_psi(200.0) - 2900.76) < 0.1

    def test_m3d_to_stbd(self):
        assert abs(_m3d_to_stbd(1.0) - 6.28981) < 0.001


# ═══════════════════════════════════════════════════════════════════════════
# Deck Generator Tests (#164)
# ═══════════════════════════════════════════════════════════════════════════

class TestDeckGenerator:
    """Tests for Eclipse .DATA deck generation."""

    def test_generates_valid_sections(self, simple_request):
        """Deck contains all required Eclipse sections."""
        deck = generate_deck(simple_request)
        for section in ["RUNSPEC", "GRID", "PROPS", "SOLUTION", "SUMMARY", "SCHEDULE"]:
            assert section in deck, f"Missing section: {section}"

    def test_runspec_dimensions(self, simple_request):
        """DIMENS keyword matches grid parameters."""
        deck = generate_deck(simple_request)
        assert "10 10 3 /" in deck  # nx ny nz

    def test_runspec_title(self, simple_request):
        """Title appears in deck."""
        deck = generate_deck(simple_request)
        assert "Test Simulation" in deck

    def test_grid_section_properties(self, simple_request):
        """GRID section has DX, DY, DZ, TOPS, PORO, PERMX."""
        deck = generate_deck(simple_request)
        for keyword in ["DX", "DY", "DZ", "TOPS", "PORO", "PERMX", "PERMY", "PERMZ"]:
            assert keyword in deck, f"Missing GRID keyword: {keyword}"

    def test_grid_cell_count(self, simple_request):
        """Grid properties have correct cell count."""
        deck = generate_deck(simple_request)
        n_cells = 10 * 10 * 3  # 300
        # Should appear as "300*value"
        assert f"{n_cells}*" in deck

    def test_grid_unit_conversion(self, simple_request):
        """DX/DY/DZ are converted from meters to feet."""
        deck = generate_deck(simple_request)
        dx_ft = _m_to_ft(100.0)
        assert f"{dx_ft:.2f}" in deck

    def test_props_section_has_relperm(self, simple_request):
        """PROPS section contains SWOF relative permeability table."""
        deck = generate_deck(simple_request)
        assert "SWOF" in deck
        assert "PVTW" in deck
        assert "DENSITY" in deck

    def test_solution_equil(self, simple_request):
        """SOLUTION section has EQUIL keyword."""
        deck = generate_deck(simple_request)
        assert "EQUIL" in deck

    def test_schedule_wells(self, simple_request):
        """SCHEDULE section defines both wells."""
        deck = generate_deck(simple_request)
        assert "'PROD'" in deck
        assert "'INJ'" in deck
        assert "WELSPECS" in deck
        assert "COMPDAT" in deck
        assert "WCONPROD" in deck
        assert "WCONINJE" in deck

    def test_schedule_timesteps(self, simple_request):
        """TSTEP keyword has correct timestep values."""
        deck = generate_deck(simple_request)
        assert "TSTEP" in deck
        # First timestep should be 30 days
        assert "30.0" in deck

    def test_deck_ends_with_end(self, simple_request):
        """Deck must end with END keyword."""
        deck = generate_deck(simple_request)
        assert deck.strip().endswith("END")

    def test_summary_requests_well_data(self, simple_request):
        """SUMMARY section requests per-well data."""
        deck = generate_deck(simple_request)
        assert "WOPR" in deck
        assert "WBHP" in deck
        assert "FOPR" in deck

    def test_write_deck_to_file(self, simple_request):
        """write_deck creates a valid file."""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "TEST.DATA")
            result = write_deck(simple_request, path)
            assert os.path.exists(result)
            content = open(result).read()
            assert "RUNSPEC" in content
            assert "END" in content.strip()

    def test_minimal_request(self):
        """Minimal request with one well produces valid deck."""
        req = SimRequest(
            wells=[
                WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0, bhp_bar=100),
            ],
            timesteps_days=[365],
        )
        deck = generate_deck(req)
        assert "RUNSPEC" in deck
        assert "'P1'" in deck

    def test_custom_grid_sizes(self):
        """Non-default grid sizes are correctly encoded."""
        req = SimRequest(
            grid=GridParams(nx=20, ny=15, nz=5, dx=50, dy=50, dz=5),
            wells=[
                WellConfig(name="P1", well_type=WellType.PRODUCER, i=19, j=14, bhp_bar=100),
            ],
        )
        deck = generate_deck(req)
        assert "20 15 5 /" in deck

    def test_gas_phase_detection(self):
        """Gas phase is added when wells inject gas."""
        req = SimRequest(
            wells=[
                WellConfig(
                    name="GINJ", well_type=WellType.INJECTOR, i=0, j=0,
                    rate_m3_day=1000, phases=[Phase.GAS],
                ),
                WellConfig(name="P1", well_type=WellType.PRODUCER, i=9, j=9, bhp_bar=100),
            ],
        )
        deck = generate_deck(req)
        assert "GAS" in deck
        assert "DISGAS" in deck


# ═══════════════════════════════════════════════════════════════════════════
# OPM Backend Tests (#163)
# ═══════════════════════════════════════════════════════════════════════════

class TestOPMBackendMetadata:
    """Test OPM backend metadata and configuration."""

    def test_name(self, opm_backend):
        assert opm_backend.name == "opm"

    def test_adapter_type(self, opm_backend):
        assert opm_backend.adapter_type == "simulator"

    def test_version_returns_string(self, opm_backend):
        v = opm_backend.version
        assert isinstance(v, str)
        # Will be "not-installed" in CI without flow binary
        assert len(v) > 0

    def test_info_includes_version(self, opm_backend):
        info = opm_backend.info()
        assert "version" in info
        assert info["name"] == "opm"
        assert info["adapter_type"] == "simulator"


class TestOPMBackendValidation:
    """Test input validation logic."""

    def test_valid_request(self, opm_backend, simple_request):
        errors = opm_backend.validate(simple_request)
        assert errors == []

    def test_grid_too_large(self, opm_backend):
        req = SimRequest(
            grid=GridParams(nx=200, ny=200, nz=10),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
        )
        errors = opm_backend.validate(req)
        assert any("100,000" in e or "100000" in e for e in errors)

    def test_well_out_of_bounds_i(self, opm_backend):
        req = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=5, j=0)],
        )
        errors = opm_backend.validate(req)
        assert any("i=" in e for e in errors)

    def test_well_out_of_bounds_j(self, opm_backend):
        req = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=5)],
        )
        errors = opm_backend.validate(req)
        assert any("j=" in e for e in errors)

    def test_well_out_of_bounds_k(self, opm_backend):
        req = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=3),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0, k_bottom=3)],
        )
        errors = opm_backend.validate(req)
        assert any("k_bottom" in e for e in errors)

    def test_no_timesteps(self, opm_backend):
        req = SimRequest(
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
            timesteps_days=[],
        )
        errors = opm_backend.validate(req)
        assert any("timestep" in e.lower() for e in errors)

    def test_negative_timestep(self, opm_backend):
        req = SimRequest(
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
            timesteps_days=[-10, 30],
        )
        errors = opm_backend.validate(req)
        assert any("positive" in e.lower() for e in errors)


class TestOPMBackendRun:
    """Test run() behavior (mocked subprocess)."""

    def test_run_creates_deck_file(self, opm_backend, simple_request):
        """run() writes a .DATA file to work_dir."""
        with tempfile.TemporaryDirectory() as td:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,  # Will fail but deck should exist
                    stdout="", stderr="flow not found",
                )
                try:
                    opm_backend.run(simple_request, td)
                except RuntimeError:
                    pass

            # Check deck was written
            deck_file = os.path.join(td, "CLARISSA_SIM.DATA")
            assert os.path.exists(deck_file)
            content = open(deck_file).read()
            assert "RUNSPEC" in content

    def test_run_calls_flow_binary(self, opm_backend, simple_request):
        """run() invokes the flow binary."""
        with tempfile.TemporaryDirectory() as td:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="Simulation complete", stderr="",
                )
                raw = opm_backend.run(simple_request, td)

            # Verify flow was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "flow" in cmd[0]

    def test_run_progress_callback(self, opm_backend, simple_request):
        """run() calls on_progress with percentages."""
        progress = []
        with tempfile.TemporaryDirectory() as td:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="", stderr="",
                )
                opm_backend.run(simple_request, td, on_progress=progress.append)

        assert 0 in progress
        assert 10 in progress  # After deck generation
        assert 90 in progress  # After flow run

    def test_run_timeout_raises(self, opm_backend, simple_request):
        """Timeout produces RuntimeError."""
        import subprocess as sp
        with tempfile.TemporaryDirectory() as td:
            with patch("subprocess.run", side_effect=sp.TimeoutExpired("flow", 60)):
                with pytest.raises(RuntimeError, match="timeout"):
                    opm_backend.run(simple_request, td)

    def test_run_binary_not_found_raises(self, opm_backend, simple_request):
        """Missing flow binary produces RuntimeError."""
        with tempfile.TemporaryDirectory() as td:
            with patch("subprocess.run", side_effect=FileNotFoundError):
                with pytest.raises(RuntimeError, match="not found"):
                    opm_backend.run(simple_request, td)


class TestOPMBackendParseResult:
    """Test parse_result() logic."""

    def test_failed_result(self, opm_backend, simple_request):
        """Failed simulation returns FAILED status."""
        raw = {
            "converged": False,
            "errors": ["Linear solver diverged"],
            "wall_time_seconds": 5.0,
        }
        result = opm_backend.parse_result(raw, simple_request)
        assert result.status == SimStatus.FAILED
        assert not result.metadata.converged
        assert result.timesteps == []

    def test_successful_result_without_files(self, opm_backend, simple_request):
        """Converged but no output files returns empty timesteps."""
        raw = {
            "converged": True,
            "output_files": {},
            "work_dir": "/tmp/test",
            "case_name": "TEST",
            "wall_time_seconds": 10.0,
            "job_id": "test-001",
        }
        result = opm_backend.parse_result(raw, simple_request)
        assert result.status == SimStatus.COMPLETED
        assert result.metadata.backend == "opm"


# ═══════════════════════════════════════════════════════════════════════════
# SPE1 Reference Data Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSPE1Reference:
    """Tests using OPM SPE1 reference output data.

    These tests validate that our parser correctly reads known reference
    data from the SPE1 benchmark case. Skipped if reference data not available.
    """

    def test_parse_restart_pressure(self, spe1_ref_dir, opm_backend):
        """Parse pressure from SPE1 UNRST reference."""
        if not spe1_ref_dir:
            pytest.skip("SPE1 reference data not available")

        unrst_path = os.path.join(spe1_ref_dir, "SPE1CASE1.UNRST")

        # Use the SPE1 grid (10x10x3)
        spe1_request = SimRequest(
            grid=GridParams(nx=10, ny=10, nz=3),
            wells=[
                WellConfig(name="PROD", well_type=WellType.PRODUCER, i=9, j=9, k_top=2, k_bottom=2),
                WellConfig(name="INJ", well_type=WellType.INJECTOR, i=0, j=0, k_top=0, k_bottom=0),
            ],
            timesteps_days=[365 * i for i in range(1, 11)],
        )

        timesteps = opm_backend._parse_restart(unrst_path, spe1_request)
        assert len(timesteps) > 0

        # First timestep should have 300 cells of pressure data
        first = timesteps[0]
        assert len(first.cells.pressure) == 300

        # Initial pressure should be ~4800 psia (SPE1 initial condition)
        p_max = max(first.cells.pressure)
        assert p_max > 4000, f"Max pressure {p_max} too low for SPE1"
        assert p_max <= 4900, f"Max pressure {p_max} too high for SPE1"

    def test_parse_restart_saturation(self, spe1_ref_dir, opm_backend):
        """Parse SGAS from SPE1 UNRST — last step should have free gas."""
        if not spe1_ref_dir:
            pytest.skip("SPE1 reference data not available")

        unrst_path = os.path.join(spe1_ref_dir, "SPE1CASE1.UNRST")
        spe1_request = SimRequest(
            grid=GridParams(nx=10, ny=10, nz=3),
            wells=[
                WellConfig(name="PROD", well_type=WellType.PRODUCER, i=9, j=9),
                WellConfig(name="INJ", well_type=WellType.INJECTOR, i=0, j=0),
            ],
            timesteps_days=[3650],
        )

        timesteps = opm_backend._parse_restart(unrst_path, spe1_request)
        last = timesteps[-1]

        # SPE1 has gas saturation at final step (gas injection)
        if last.cells.saturation_gas:
            sg_max = max(last.cells.saturation_gas)
            assert sg_max > 0.01, "Expected free gas at final SPE1 timestep"

    def test_parse_summary_production(self, spe1_ref_dir, opm_backend):
        """Parse FOPR from SPE1 summary — known reference values."""
        if not spe1_ref_dir:
            pytest.skip("SPE1 reference data not available")

        smspec_path = os.path.join(spe1_ref_dir, "SPE1CASE1.SMSPEC")
        spe1_request = SimRequest(
            grid=GridParams(nx=10, ny=10, nz=3),
            wells=[
                WellConfig(name="PROD", well_type=WellType.PRODUCER, i=9, j=9),
                WellConfig(name="INJ", well_type=WellType.INJECTOR, i=0, j=0),
            ],
        )

        summary = opm_backend._parse_summary(smspec_path, spe1_request)

        # Should have TIME and FOPR
        assert "TIME" in summary
        assert "FOPR" in summary

        # SPE1 FOPR reference: starts at 20000 STB/day, declines to ~5558
        fopr = summary["FOPR"]
        assert max(fopr) == pytest.approx(20000, abs=100)

        # Final FOPR should be around 5558 STB/day
        assert fopr[-1] == pytest.approx(5558, abs=200)

    def test_parse_summary_bhp(self, spe1_ref_dir, opm_backend):
        """Parse WBHP from SPE1 — BHP lower limit is 1000 psia."""
        if not spe1_ref_dir:
            pytest.skip("SPE1 reference data not available")

        smspec_path = os.path.join(spe1_ref_dir, "SPE1CASE1.SMSPEC")
        spe1_request = SimRequest(
            grid=GridParams(nx=10, ny=10, nz=3),
            wells=[
                WellConfig(name="PROD", well_type=WellType.PRODUCER, i=9, j=9),
                WellConfig(name="INJ", well_type=WellType.INJECTOR, i=0, j=0),
            ],
        )

        summary = opm_backend._parse_summary(smspec_path, spe1_request)

        # Producer BHP should hit minimum 1000 psia
        if "WBHP:PROD" in summary:
            bhp_prod = summary["WBHP:PROD"]
            assert min(bhp_prod) == pytest.approx(1000, abs=10)

    def test_egrid_dimensions(self, spe1_ref_dir):
        """Verify EGrid reading gives correct dimensions."""
        if not spe1_ref_dir:
            pytest.skip("SPE1 reference data not available")

        try:
            from opm.io.ecl import EGrid
        except ImportError:
            pytest.skip("opm.io.ecl not available")

        egrid_path = os.path.join(spe1_ref_dir, "SPE1CASE1.EGRID")
        grid = EGrid(egrid_path)
        assert grid.dimension == [10, 10, 3]


# ═══════════════════════════════════════════════════════════════════════════
# API Tests (#165)
# ═══════════════════════════════════════════════════════════════════════════

class TestSimAPI:
    """Test FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[testclient] not available")

        from clarissa.sim_engine.sim_api import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """GET /health returns status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "backends" in data
        assert "active_jobs" in data

    def test_list_jobs_empty(self, client):
        """GET /sim/list returns empty list initially."""
        resp = client.get("/sim/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_submit_invalid_backend(self, client):
        """POST /sim/run with unknown backend returns 400."""
        resp = client.post("/sim/run", json={
            "backend": "nonexistent",
            "wells": [{"name": "P1", "well_type": "producer", "i": 0, "j": 0}],
        })
        assert resp.status_code == 400

    def test_get_nonexistent_job(self, client):
        """GET /sim/unknown returns 404."""
        resp = client.get("/sim/unknown-job-id")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# Integration: Mock Backend end-to-end
# ═══════════════════════════════════════════════════════════════════════════

class TestMockBackendIntegration:
    """End-to-end tests using the mock backend from test_sim_engine.py."""

    def test_full_pipeline_mock(self, simple_request):
        """Mock backend: validate → run → parse_result → UnifiedResult."""
        # Import the mock from existing tests
        from tests.test_sim_engine import MockBackend

        backend = MockBackend()

        # Validate
        errors = backend.validate(simple_request)
        assert errors == []

        # Run
        with tempfile.TemporaryDirectory() as td:
            raw = backend.run(simple_request, td)

        # Parse
        result = backend.parse_result(raw, simple_request)

        assert isinstance(result, UnifiedResult)
        assert result.status == SimStatus.COMPLETED
        assert result.metadata.converged
        assert len(result.timesteps) == len(simple_request.timesteps_days)

        # Verify well data
        last = result.last_timestep
        assert len(last.wells) == 2
        prod = next(w for w in last.wells if w.well_name == "PROD")
        assert prod.oil_rate_m3_day > 0

    def test_result_json_roundtrip(self, simple_request):
        """UnifiedResult serializes and deserializes correctly."""
        from tests.test_sim_engine import MockBackend

        backend = MockBackend()
        raw = backend.run(simple_request, "/tmp/test")
        result = backend.parse_result(raw, simple_request)

        # JSON roundtrip
        json_str = result.model_dump_json()
        result2 = UnifiedResult.model_validate_json(json_str)

        assert result2.job_id == result.job_id
        assert len(result2.timesteps) == len(result.timesteps)
        assert result2.metadata.backend == result.metadata.backend


# ═══════════════════════════════════════════════════════════════════════════
# Deck Generator Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestDeckGeneratorEdgeCases:
    """Edge cases and robustness tests for deck generation."""

    def test_single_cell_grid(self):
        """1x1x1 grid produces valid deck."""
        req = SimRequest(
            grid=GridParams(nx=1, ny=1, nz=1),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
        )
        deck = generate_deck(req)
        assert "1 1 1 /" in deck
        assert "1*" in deck  # 1 cell

    def test_many_wells(self):
        """Multiple wells are all included."""
        wells = [
            WellConfig(name=f"W{i}", well_type=WellType.PRODUCER, i=i, j=0, bhp_bar=100)
            for i in range(5)
        ]
        req = SimRequest(
            grid=GridParams(nx=10, ny=10, nz=1),
            wells=wells,
        )
        deck = generate_deck(req)
        for w in wells:
            assert f"'{w.name}'" in deck

    def test_large_timesteps(self):
        """Long simulation period (10 years)."""
        req = SimRequest(
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
            timesteps_days=[365 * i for i in range(1, 11)],
        )
        deck = generate_deck(req)
        assert "TSTEP" in deck
        # First increment should be 365 days
        assert "365.0" in deck

    def test_custom_fluid_properties(self):
        """Custom FluidProperties are reflected in deck."""
        req = SimRequest(
            fluid=FluidProperties(
                oil_density_kg_m3=850,
                water_density_kg_m3=1020,
                oil_viscosity_cp=2.0,
                water_viscosity_cp=0.3,
            ),
            wells=[WellConfig(name="P1", well_type=WellType.PRODUCER, i=0, j=0)],
        )
        deck = generate_deck(req)
        # Check oil viscosity appears in PVT data
        assert "2.0" in deck or "2.00" in deck

    def test_deck_no_terminator_issues(self, simple_request):
        """Deck has proper '/' terminators for all keywords."""
        deck = generate_deck(simple_request)
        # Count slashes — should be substantial (each keyword needs termination)
        slash_count = deck.count(" /")
        assert slash_count >= 10, f"Only {slash_count} terminators found"


# ═══════════════════════════════════════════════════════════════════════════
# OPM Backend Helper Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestOPMBackendHelpers:
    """Test internal helper methods."""

    def test_step_to_days_linear(self):
        """Step-to-day conversion is linear interpolation."""
        days = OPMBackend._step_to_days(50, list(range(101)), [3650])
        assert days == pytest.approx(1825, abs=1)  # Halfway

    def test_step_to_days_zero(self):
        """Step 0 maps to day 0."""
        days = OPMBackend._step_to_days(0, [0, 1, 2], [365])
        assert days == 0.0

    def test_step_to_days_empty(self):
        """Empty inputs handled gracefully."""
        days = OPMBackend._step_to_days(5, [], [])
        assert days == 5.0

    def test_safe_get_valid(self):
        """safe_get returns value at index."""
        data = {"key": [10.0, 20.0, 30.0]}
        assert OPMBackend._safe_get(data, "key", 1) == 20.0

    def test_safe_get_missing_key(self):
        """safe_get returns default for missing key."""
        assert OPMBackend._safe_get({}, "missing", 0, -1.0) == -1.0

    def test_safe_get_out_of_bounds(self):
        """safe_get returns default for out-of-bounds index."""
        data = {"key": [10.0]}
        assert OPMBackend._safe_get(data, "key", 5, 0.0) == 0.0
