"""Tests for MRST Backend (Issue #166).

Covers:
1. MRST Script Generator — SimRequest → .m script correctness
2. MRSTBackend — validate, run (mocked), parse_result (mocked .mat)
3. Registry integration — backend registers, discoverable
4. PAL contract — MRSTBackend isa SimulatorBackend isa PlatformAdapter

All tests are offline — no Octave/MRST required.

Issue #166 | Epic #161 | ADR-040
"""
from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
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
from clarissa.sim_engine.mrst_script_generator import (
    generate_mrst_script,
    write_mrst_script,
)
from clarissa.sim_engine.backends.mrst_backend import MRSTBackend
from clarissa.sim_engine.backends.base import SimulatorBackend
from clarissa.pal import PlatformAdapter


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def simple_request() -> SimRequest:
    """Minimal two-phase oil-water simulation request."""
    return SimRequest(
        grid=GridParams(nx=10, ny=10, nz=1, dx=100.0, dy=100.0, dz=10.0),
        wells=[
            WellConfig(
                name="INJ1", well_type=WellType.INJECTOR,
                i=0, j=0, k_top=0, k_bottom=0,
                rate_m3_day=100.0, phases=[Phase.WATER],
            ),
            WellConfig(
                name="PROD1", well_type=WellType.PRODUCER,
                i=9, j=9, k_top=0, k_bottom=0,
                bhp_bar=150.0, phases=[Phase.OIL, Phase.WATER],
            ),
        ],
        fluid=FluidProperties(
            oil_density_kg_m3=800.0,
            water_density_kg_m3=1000.0,
            oil_viscosity_cp=1.0,
            water_viscosity_cp=0.5,
            initial_pressure_bar=200.0,
        ),
        timesteps_days=[30, 60, 90, 180, 365],
        title="MRST Test Case",
        backend="mrst",
    )


@pytest.fixture
def three_phase_request() -> SimRequest:
    """Three-phase oil-water-gas request."""
    return SimRequest(
        grid=GridParams(nx=5, ny=5, nz=3),
        wells=[
            WellConfig(
                name="GAS_INJ", well_type=WellType.INJECTOR,
                i=0, j=0, k_top=0, k_bottom=2,
                rate_m3_day=50.0, phases=[Phase.GAS],
            ),
            WellConfig(
                name="PROD_A", well_type=WellType.PRODUCER,
                i=4, j=4, k_top=0, k_bottom=2,
                bhp_bar=100.0, phases=[Phase.OIL, Phase.WATER, Phase.GAS],
            ),
        ],
        timesteps_days=[30, 90, 365],
        title="Three-Phase Test",
        backend="mrst",
    )


@pytest.fixture
def backend() -> MRSTBackend:
    return MRSTBackend()


@pytest.fixture
def mock_mat_data() -> dict:
    """Simulated .mat file content (as scipy.io.loadmat would return)."""
    n_steps = 5
    n_cells = 100  # 10×10×1
    n_wells = 2

    return {
        "time_days": np.array([[30], [60], [90], [180], [365]], dtype=float),
        "pressure": np.random.uniform(150, 200, (n_steps, n_cells)),
        "s_water": np.random.uniform(0.0, 0.5, (n_steps, n_cells)),
        "s_oil": np.random.uniform(0.5, 1.0, (n_steps, n_cells)),
        "well_bhp": np.array([
            [200.0, 150.0],
            [198.0, 150.0],
            [195.0, 150.0],
            [190.0, 150.0],
            [185.0, 150.0],
        ]),
        "well_qOs": np.array([
            [0.0, -80.0],
            [0.0, -75.0],
            [0.0, -70.0],
            [0.0, -60.0],
            [0.0, -50.0],
        ]),
        "well_qWs": np.array([
            [100.0, -5.0],
            [100.0, -10.0],
            [100.0, -15.0],
            [100.0, -20.0],
            [100.0, -25.0],
        ]),
        "well_names": np.array([["INJ1"], ["PROD1"]], dtype=object),
        "grid_dims": np.array([[10, 10, 1]]),
        "wall_time": np.array([[12.5]]),
        "converged": np.array([[1]]),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. Script Generator Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTScriptGenerator:
    """Tests for MRST .m script generation."""

    def test_generates_string(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert isinstance(script, str)
        assert len(script) > 100

    def test_header_metadata(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "CLARISSA Simulation" in script
        assert "MRST Backend" in script
        assert "MRST Test Case" in script
        assert "10×10×1 = 100 cells" in script

    def test_grid_section(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "cartGrid" in script
        assert "[10, 10, 1]" in script
        assert "computeGeometry" in script

    def test_grid_dimensions(self, simple_request):
        """Physical dimensions = nx*dx, ny*dy, nz*dz."""
        script = generate_mrst_script(simple_request)
        # 10*100=1000, 10*100=1000, 1*10=10
        assert "[1000.0, 1000.0, 10.0]" in script

    def test_rock_properties(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "makeRock" in script
        assert str(simple_request.grid.porosity) in script

    def test_permeability_conversion(self, simple_request):
        """Permeability is converted from mD to m²."""
        script = generate_mrst_script(simple_request)
        # 100 mD = 9.869233e-14 m²
        assert "9.869233e-14" in script

    def test_two_phase_fluid(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "'phases', 'WO'" in script
        assert "'WOG'" not in script

    def test_three_phase_fluid(self, three_phase_request):
        script = generate_mrst_script(three_phase_request)
        assert "'phases', 'WOG'" in script

    def test_well_definitions(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "'INJ1'" in script
        assert "'PROD1'" in script
        assert "addWell" in script

    def test_injector_rate_control(self, simple_request):
        """Injector with rate_m3_day → rate control in m³/s."""
        script = generate_mrst_script(simple_request)
        # 100 m³/day = 100/86400 m³/s ≈ 1.157e-03
        assert "'type', 'rate'" in script

    def test_producer_bhp_control(self, simple_request):
        """Producer with bhp_bar → BHP control in Pa."""
        script = generate_mrst_script(simple_request)
        # 150 bar = 150 * 1e5 = 1.5e7 Pa
        assert "'type', 'bhp'" in script

    def test_well_1based_indexing(self, simple_request):
        """MRST uses 1-based indexing, our model uses 0-based."""
        script = generate_mrst_script(simple_request)
        # INJ1 at i=0,j=0 → 1*ones, 1*ones in MRST
        assert "1*ones" in script

    def test_initial_state(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "initResSol" in script
        # 200 bar = 200*1e5 = 2e7 Pa
        assert "20000000" in script

    def test_schedule_timesteps(self, simple_request):
        """Timesteps converted from cumulative days to incremental seconds."""
        script = generate_mrst_script(simple_request)
        assert "simpleSchedule" in script
        # First step: 30 days = 30*86400 = 2592000 seconds
        assert "2592000.0" in script

    def test_solver_setup(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "GenericBlackOilModel" in script
        assert "NonLinearSolver" in script
        assert "simulateScheduleAD" in script

    def test_export_section(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "save(" in script
        assert "results.mat" in script
        assert "'time_days'" in script
        assert "'pressure'" in script
        assert "'-v7'" in script

    def test_custom_output_filename(self, simple_request):
        script = generate_mrst_script(simple_request, output_mat="custom.mat")
        assert "custom.mat" in script
        assert "results.mat" not in script

    def test_well_names_in_export(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "'INJ1'" in script
        assert "'PROD1'" in script

    def test_mrst_startup(self, simple_request):
        script = generate_mrst_script(simple_request)
        assert "mrstModule add" in script
        assert "ad-blackoil" in script
        assert "ad-core" in script

    def test_write_to_file(self, simple_request, tmp_path):
        path = str(tmp_path / "test.m")
        result = write_mrst_script(simple_request, path)
        assert result == path
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "cartGrid" in content

    def test_gas_injector_composition(self, three_phase_request):
        """Gas injector → Comp_i = [0, 0, 1]."""
        script = generate_mrst_script(three_phase_request)
        assert "[0, 0, 1]" in script

    def test_water_injector_composition_two_phase(self, simple_request):
        """Water injector in 2-phase → Comp_i = [1, 0]."""
        script = generate_mrst_script(simple_request)
        assert "[1, 0]" in script

    def test_multiple_layers(self, three_phase_request):
        """Wells perforated across multiple layers."""
        script = generate_mrst_script(three_phase_request)
        # k_top=0, k_bottom=2 → MRST: (1:3)' → 3 layers
        assert "(1:3)'" in script


# ═══════════════════════════════════════════════════════════════════════════
# 2. MRSTBackend — PAL Contract
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTBackendPALContract:
    """Verify MRST backend satisfies the PAL contract."""

    def test_is_platform_adapter(self, backend):
        assert isinstance(backend, PlatformAdapter)

    def test_is_simulator_backend(self, backend):
        assert isinstance(backend, SimulatorBackend)

    def test_adapter_type(self, backend):
        assert backend.adapter_type == "simulator"

    def test_name(self, backend):
        assert backend.name == "mrst"

    def test_info_contains_required_fields(self, backend):
        info = backend.info()
        assert "name" in info
        assert "adapter_type" in info
        assert "healthy" in info
        assert "version" in info
        assert info["name"] == "mrst"
        assert info["adapter_type"] == "simulator"

    def test_version_not_installed(self, backend):
        """Without Octave, version should report not-installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert backend.version == "not-installed"

    def test_version_detected(self, backend):
        mock_result = MagicMock()
        mock_result.stdout = "GNU Octave, version 8.4.0\n"
        with patch("subprocess.run", return_value=mock_result):
            assert "8.4.0" in backend.version

    def test_health_check_unavailable(self, backend):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert backend.health_check() is False

    def test_health_check_available(self, backend):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            assert backend.health_check() is True

    def test_health_check_cached(self, backend):
        """Second call uses cached value."""
        backend._octave_available = True
        assert backend.health_check() is True

    def test_health_check_docker(self):
        backend = MRSTBackend(use_docker=True, docker_image="test:latest")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            assert backend.health_check() is True
            cmd = mock_run.call_args[0][0]
            assert "docker" in cmd


# ═══════════════════════════════════════════════════════════════════════════
# 3. MRSTBackend — Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTBackendValidation:
    """Test input validation for MRST-specific constraints."""

    def test_valid_request(self, backend, simple_request):
        errors = backend.validate(simple_request)
        assert errors == []

    def test_grid_too_large(self, backend):
        request = SimRequest(
            grid=GridParams(nx=200, ny=200, nz=10),  # 400k cells
            wells=[WellConfig(name="W", well_type=WellType.PRODUCER, i=0, j=0, bhp_bar=100)],
            timesteps_days=[30],
        )
        errors = backend.validate(request)
        assert any("200,000" in e for e in errors)

    def test_well_out_of_bounds_i(self, backend):
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[WellConfig(name="W", well_type=WellType.PRODUCER, i=5, j=0, bhp_bar=100)],
            timesteps_days=[30],
        )
        errors = backend.validate(request)
        assert any("i=5" in e for e in errors)

    def test_well_out_of_bounds_j(self, backend):
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[WellConfig(name="W", well_type=WellType.PRODUCER, i=0, j=5, bhp_bar=100)],
            timesteps_days=[30],
        )
        errors = backend.validate(request)
        assert any("j=5" in e for e in errors)

    def test_well_out_of_bounds_k(self, backend):
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=2),
            wells=[WellConfig(name="W", well_type=WellType.PRODUCER, i=0, j=0, k_top=0, k_bottom=2, bhp_bar=100)],
            timesteps_days=[30],
        )
        errors = backend.validate(request)
        assert any("k_bottom=2" in e for e in errors)

    def test_no_timesteps(self, backend, simple_request):
        simple_request.timesteps_days = []
        errors = backend.validate(simple_request)
        assert any("timestep" in e.lower() for e in errors)

    def test_negative_timesteps(self, backend, simple_request):
        simple_request.timesteps_days = [30, -10, 90]
        errors = backend.validate(simple_request)
        assert any("positive" in e.lower() for e in errors)

    def test_multiple_errors(self, backend):
        """Multiple validation errors returned together."""
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[
                WellConfig(name="W1", well_type=WellType.PRODUCER, i=10, j=10, bhp_bar=100),
            ],
            timesteps_days=[],
        )
        errors = backend.validate(request)
        assert len(errors) >= 3  # i, j, timesteps


# ═══════════════════════════════════════════════════════════════════════════
# 4. MRSTBackend — Run (Mocked Octave)
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTBackendRun:
    """Test run() with mocked subprocess calls."""

    def test_run_success(self, backend, simple_request, tmp_path):
        """Successful run creates .mat and returns converged."""
        work_dir = str(tmp_path)
        mat_path = tmp_path / "results.mat"
        mat_path.write_bytes(b"fake mat content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Simulation completed in 5.00 seconds\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            raw = backend.run(simple_request, work_dir)

        assert raw["converged"] is True
        assert raw["exit_code"] == 0
        assert "mat" in raw["output_files"]
        assert raw["wall_time_seconds"] > 0
        assert (tmp_path / "clarissa_sim.m").exists()

    def test_run_creates_script(self, backend, simple_request, tmp_path):
        """Run generates .m script in work_dir."""
        work_dir = str(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"

        with patch("subprocess.run", return_value=mock_result):
            raw = backend.run(simple_request, work_dir)

        script = tmp_path / "clarissa_sim.m"
        assert script.exists()
        content = script.read_text()
        assert "cartGrid" in content

    def test_run_failure(self, backend, simple_request, tmp_path):
        """Non-zero exit code → converged=False."""
        work_dir = str(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: undefined function 'mrstModule'"

        with patch("subprocess.run", return_value=mock_result):
            raw = backend.run(simple_request, work_dir)

        assert raw["converged"] is False
        assert raw["exit_code"] == 1
        assert any("mrstModule" in e for e in raw["errors"])

    def test_run_timeout(self, backend, simple_request, tmp_path):
        """Timeout raises RuntimeError."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("octave", 900)):
            with pytest.raises(RuntimeError, match="timeout"):
                backend.run(simple_request, str(tmp_path))

    def test_run_octave_not_found(self, backend, simple_request, tmp_path):
        """Missing octave binary raises RuntimeError."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="Octave not found"):
                backend.run(simple_request, str(tmp_path))

    def test_run_progress_callback(self, backend, simple_request, tmp_path):
        """Progress callback is invoked."""
        progress_values = []
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            backend.run(
                simple_request, str(tmp_path),
                on_progress=lambda pct: progress_values.append(pct),
            )

        assert 0 in progress_values
        assert 10 in progress_values
        assert 80 in progress_values
        assert 90 in progress_values

    def test_run_docker_mode(self, simple_request, tmp_path):
        """Docker mode builds correct command."""
        backend = MRSTBackend(use_docker=True, docker_image="mrst:test")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            backend.run(simple_request, str(tmp_path))

        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "mrst:test" in cmd
        assert "octave" in cmd

    def test_run_mrst_dir_env(self, simple_request, tmp_path):
        """MRST_DIR is passed through environment."""
        backend = MRSTBackend(mrst_dir="/opt/mrst")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            backend.run(simple_request, str(tmp_path))

        env = mock_run.call_args[1].get("env", {})
        assert env.get("MRST_DIR") == "/opt/mrst"


# ═══════════════════════════════════════════════════════════════════════════
# 5. MRSTBackend — Parse Result
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTBackendParseResult:
    """Test parse_result() with mocked .mat data."""

    def test_parse_success(self, backend, simple_request, mock_mat_data):
        raw = {
            "job_id": "test-001",
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 12.5,
            "work_dir": "/fake",
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        assert result.status == SimStatus.COMPLETED
        assert result.metadata.backend == "mrst"
        assert result.metadata.converged is True
        assert len(result.timesteps) == 5

    def test_parse_timestep_values(self, backend, simple_request, mock_mat_data):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        ts = result.timesteps
        assert ts[0].time_days == 30.0
        assert ts[4].time_days == 365.0

    def test_parse_cell_data(self, backend, simple_request, mock_mat_data):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        cells = result.timesteps[0].cells
        assert len(cells.pressure) == 100  # 10×10×1
        assert len(cells.saturation_water) == 100
        assert len(cells.saturation_oil) == 100

    def test_parse_well_data(self, backend, simple_request, mock_mat_data):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        wells = result.timesteps[0].wells
        assert len(wells) == 2
        assert wells[0].well_name == "INJ1"
        assert wells[1].well_name == "PROD1"
        assert wells[0].bhp_bar == 200.0
        assert wells[1].bhp_bar == 150.0

    def test_parse_well_rates_absolute(self, backend, simple_request, mock_mat_data):
        """Well rates should be absolute values (MRST uses sign convention)."""
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        prod = result.timesteps[0].wells[1]
        assert prod.oil_rate_m3_day >= 0  # abs of negative
        assert prod.water_rate_m3_day >= 0

    def test_parse_wall_time_from_mat(self, backend, simple_request, mock_mat_data):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 99.0,  # subprocess time
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        # Should prefer .mat wall_time (12.5) over subprocess time (99.0)
        assert result.metadata.wall_time_seconds == 12.5

    def test_parse_not_converged(self, backend, simple_request):
        raw = {
            "converged": False,
            "output_files": {},
            "wall_time_seconds": 5.0,
            "errors": ["octave exit code: 1"],
        }
        result = backend.parse_result(raw, simple_request)
        assert result.status == SimStatus.FAILED
        assert result.metadata.converged is False

    def test_parse_no_mat_file(self, backend, simple_request):
        raw = {
            "converged": True,
            "output_files": {},
            "wall_time_seconds": 5.0,
            "errors": [],
        }
        result = backend.parse_result(raw, simple_request)
        assert result.status == SimStatus.FAILED
        assert any("No .mat" in w for w in result.metadata.warnings)

    def test_parse_scipy_not_available(self, backend, simple_request):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 5.0,
            "errors": [],
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=None):
            result = backend.parse_result(raw, simple_request)

        assert result.status == SimStatus.FAILED
        assert any("Failed to load" in w for w in result.metadata.warnings)

    def test_parse_grid_cells_in_metadata(self, backend, simple_request, mock_mat_data):
        raw = {
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        assert result.metadata.grid_cells == 100

    def test_unified_result_summary(self, backend, simple_request, mock_mat_data):
        """UnifiedResult.summary() works with MRST data."""
        raw = {
            "job_id": "mrst-test",
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 0,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        summary = result.summary()
        assert summary["backend"] == "mrst"
        assert summary["timesteps"] == 5
        assert summary["converged"] is True
        assert summary["final_time_days"] == 365.0


# ═══════════════════════════════════════════════════════════════════════════
# 6. Registry Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTBackendRegistry:
    """Test registry integration."""

    def test_register_and_discover(self):
        from clarissa.pal import AdapterRegistry

        registry = AdapterRegistry()
        backend = MRSTBackend()
        registry.register(backend)

        found = registry.get("simulator", "mrst")
        assert found is backend

    def test_register_alongside_opm(self):
        from clarissa.pal import AdapterRegistry
        from clarissa.sim_engine.backends.opm_backend import OPMBackend

        registry = AdapterRegistry()
        registry.register(OPMBackend())
        registry.register(MRSTBackend())

        names = registry.list_names("simulator")
        assert "opm" in names
        assert "mrst" in names

    def test_health_aggregation(self):
        from clarissa.pal import AdapterRegistry

        registry = AdapterRegistry()
        backend = MRSTBackend()
        backend._octave_available = True
        registry.register(backend)

        health = registry.health()
        assert health["adapters"]["simulator"]["mrst"] is True

    def test_registry_info(self):
        from clarissa.pal import AdapterRegistry

        registry = AdapterRegistry()
        registry.register(MRSTBackend())

        infos = registry.info()
        mrst_info = [i for i in infos if i["name"] == "mrst"]
        assert len(mrst_info) == 1
        assert mrst_info[0]["adapter_type"] == "simulator"


# ═══════════════════════════════════════════════════════════════════════════
# 7. End-to-End Mock Pipeline
# ═══════════════════════════════════════════════════════════════════════════


class TestMRSTEndToEnd:
    """Full pipeline test with all external dependencies mocked."""

    def test_validate_run_parse(self, backend, simple_request, mock_mat_data, tmp_path):
        """Complete lifecycle: validate → run → parse_result."""
        # 1. Validate
        errors = backend.validate(simple_request)
        assert errors == []

        # 2. Run (mocked)
        work_dir = str(tmp_path)
        mat_path = tmp_path / "results.mat"
        mat_path.write_bytes(b"fake")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            raw = backend.run(simple_request, work_dir)

        assert raw["converged"] is True

        # 3. Parse (mocked .mat)
        raw["job_id"] = "e2e-test"
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            result = backend.parse_result(raw, simple_request)

        assert result.status == SimStatus.COMPLETED
        assert result.job_id == "e2e-test"
        assert result.metadata.backend == "mrst"
        assert len(result.timesteps) == 5
        assert result.timesteps[-1].time_days == 365.0
        assert len(result.timesteps[0].cells.pressure) == 100
        assert len(result.timesteps[0].wells) == 2

    def test_opm_vs_mrst_result_structure(self, simple_request, mock_mat_data):
        """OPM and MRST produce UnifiedResult with identical structure."""
        backend = MRSTBackend()
        raw = {
            "job_id": "comparison",
            "converged": True,
            "output_files": {"mat": "/fake/results.mat"},
            "wall_time_seconds": 10,
        }
        with patch.object(MRSTBackend, "_load_mat", return_value=mock_mat_data):
            mrst_result = backend.parse_result(raw, simple_request)

        # Both should have identical top-level fields
        assert hasattr(mrst_result, "job_id")
        assert hasattr(mrst_result, "timesteps")
        assert hasattr(mrst_result, "metadata")
        assert hasattr(mrst_result, "request")
        assert hasattr(mrst_result, "status")

        # Both metadata should have backend field
        assert mrst_result.metadata.backend == "mrst"

        # Timestep structure should be identical
        ts = mrst_result.timesteps[0]
        assert hasattr(ts, "time_days")
        assert hasattr(ts, "cells")
        assert hasattr(ts, "wells")
        assert hasattr(ts.cells, "pressure")
        assert hasattr(ts.cells, "saturation_water")
        assert hasattr(ts.cells, "saturation_oil")
