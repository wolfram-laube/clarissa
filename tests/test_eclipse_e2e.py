"""E2E tests: Eclipse output → UnifiedResult → Comparison.

Creates synthetic Eclipse binary files (SMSPEC + UNRST) matching
SPE1 dimensions, reads them through the eclipse_reader, and validates
the complete pipeline including comparison.

Tests require: resdata, resfo, numpy

Issue #108 | Epic #161 | ADR-040
"""
from __future__ import annotations

import datetime
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from clarissa.sim_engine.eclipse_reader import (
    read_eclipse_output,
    read_restart,
    read_summary,
)
from clarissa.sim_engine.comparison import compare
from clarissa.sim_engine.models import (
    CellData,
    FluidProperties,
    GridParams,
    Phase,
    SimRequest,
    SimStatus,
    TimestepResult,
    UnifiedResult,
    WellConfig,
    WellType,
)


# ═══════════════════════════════════════════════════════════════════════════
# Synthetic Eclipse Data Generator
# ═══════════════════════════════════════════════════════════════════════════


def _write_synthetic_smspec(
    case_path: str,
    n_steps: int = 12,
    nx: int = 10,
    ny: int = 10,
    nz: int = 3,
    unit_system: str = "FIELD",
    pressure_start: float = 4800.0,
    pressure_decline: float = 10.0,
    oil_rate_start: float = 5000.0,
    oil_rate_decline: float = 50.0,
    seed: int = 42,
) -> str:
    """Write synthetic SMSPEC/UNSMRY files.

    Returns path to SMSPEC file.
    """
    from resdata.summary import Summary

    rng = np.random.RandomState(seed)
    start = datetime.datetime(2025, 1, 1)

    s = Summary.writer(case_path, start, nx, ny, nz)

    # Field variables
    s.add_variable("FOPR")
    s.add_variable("FWPR")
    s.add_variable("FGPR")
    s.add_variable("FPR")
    s.add_variable("FOPT")
    s.add_variable("FWPT")

    # Well variables
    for var in ["WOPR", "WWPR", "WGPR", "WBHP"]:
        s.add_variable(var, wgname="PROD")
    for var in ["WWIR", "WGIR", "WBHP"]:
        s.add_variable(var, wgname="INJ")

    cumulative_oil = 0.0
    cumulative_water = 0.0

    for step in range(1, n_steps + 1):
        sim_days = step * 30.0
        ts = s.add_t_step(step, sim_days)

        # Declining oil rate with noise
        oil_rate = max(0, oil_rate_start - step * oil_rate_decline + rng.normal(0, 20))
        water_rate = 200 + step * 50 + rng.normal(0, 10)
        gas_rate = oil_rate * 0.5 + rng.normal(0, 5)
        pressure = pressure_start - step * pressure_decline + rng.normal(0, 5)

        cumulative_oil += oil_rate * 30
        cumulative_water += water_rate * 30

        # Field totals
        ts["FOPR"] = oil_rate
        ts["FWPR"] = water_rate
        ts["FGPR"] = gas_rate
        ts["FPR"] = pressure
        ts["FOPT"] = cumulative_oil
        ts["FWPT"] = cumulative_water

        # Producer
        ts["WOPR:PROD"] = oil_rate
        ts["WWPR:PROD"] = water_rate
        ts["WGPR:PROD"] = gas_rate
        ts["WBHP:PROD"] = max(1000, pressure - 200 + rng.normal(0, 5))

        # Injector
        ts["WWIR:INJ"] = 8000 + rng.normal(0, 50)
        ts["WGIR:INJ"] = 100000 + rng.normal(0, 500)
        ts["WBHP:INJ"] = pressure + 500 + rng.normal(0, 10)

    s.fwrite()
    return case_path + ".SMSPEC"


def _write_synthetic_unrst(
    case_path: str,
    n_steps: int = 12,
    n_cells: int = 300,
    pressure_start: float = 4800.0,
    pressure_decline: float = 10.0,
    sw_initial: float = 0.12,
    sw_increase: float = 0.005,
    seed: int = 42,
) -> str:
    """Write synthetic UNRST file with per-cell pressure and saturation.

    Returns path to UNRST file.
    """
    import resfo

    rng = np.random.RandomState(seed)
    records = []

    for step in range(1, n_steps + 1):
        # SEQNUM
        records.append(("SEQNUM  ", np.array([step], dtype=np.int32)))

        # INTEHEAD (minimal)
        intehead = np.zeros(95, dtype=np.int32)
        intehead[0] = 1  # FIELD
        intehead[64] = 2025  # year
        intehead[65] = 1 + ((step * 30) // 30 - 1) % 12  # month
        intehead[66] = 1 + (step * 30) % 28  # day
        records.append(("INTEHEAD", intehead))

        # PRESSURE: base pressure with spatial gradient + noise
        p_base = pressure_start - step * pressure_decline
        pressure = np.array([
            p_base + (i / n_cells) * 200.0 + rng.normal(0, 2)
            for i in range(n_cells)
        ], dtype=np.float32)
        records.append(("PRESSURE", pressure))

        # SWAT: increasing with time, spatial variation
        sw_base = sw_initial + step * sw_increase
        swat = np.array([
            np.clip(sw_base + (i / n_cells) * 0.08 + rng.normal(0, 0.005), 0, 1)
            for i in range(n_cells)
        ], dtype=np.float32)
        records.append(("SWAT    ", swat))

        # SGAS: small gas saturation
        sgas = np.array([
            np.clip(0.01 + rng.normal(0, 0.002), 0, 0.5)
            for _ in range(n_cells)
        ], dtype=np.float32)
        records.append(("SGAS    ", sgas))

    resfo.write(case_path + ".UNRST", records)
    return case_path + ".UNRST"


def _write_full_synthetic(
    tmp_dir: str,
    case_name: str = "SPE1_SYNTHETIC",
    n_steps: int = 12,
    nx: int = 10, ny: int = 10, nz: int = 3,
    seed: int = 42,
    **kwargs,
) -> str:
    """Write complete synthetic Eclipse output (SMSPEC + UNRST).

    Returns case base path (without extension).
    """
    case_path = os.path.join(tmp_dir, case_name)
    n_cells = nx * ny * nz

    # Split kwargs for each writer
    smspec_kw = {k: v for k, v in kwargs.items()
                 if k in ("pressure_start", "pressure_decline",
                          "oil_rate_start", "oil_rate_decline")}
    unrst_kw = {k: v for k, v in kwargs.items()
                if k in ("pressure_start", "pressure_decline",
                         "sw_initial", "sw_increase")}

    _write_synthetic_smspec(
        case_path, n_steps=n_steps, nx=nx, ny=ny, nz=nz, seed=seed, **smspec_kw
    )
    _write_synthetic_unrst(
        case_path, n_steps=n_steps, n_cells=n_cells, seed=seed, **unrst_kw
    )

    return case_path


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def spe1_request() -> SimRequest:
    """SimRequest matching SPE1 dimensions."""
    return SimRequest(
        grid=GridParams(nx=10, ny=10, nz=3, dx=304.8, dy=304.8, dz=9.144,
                        porosity=0.3, permeability_x=250),
        wells=[
            WellConfig(name="INJ", well_type=WellType.INJECTOR,
                       i=0, j=0, rate_m3_day=2831, phases=[Phase.GAS]),
            WellConfig(name="PROD", well_type=WellType.PRODUCER,
                       i=9, j=9, bhp_bar=68.9, phases=[Phase.OIL]),
        ],
        fluid=FluidProperties(initial_pressure_bar=330.95),
        timesteps_days=[float(i * 30) for i in range(1, 13)],
        title="SPE1 Synthetic",
        backend="opm",
    )


@pytest.fixture
def synthetic_case():
    """Create a full synthetic Eclipse output in a temp dir."""
    with tempfile.TemporaryDirectory() as tmp:
        case_path = _write_full_synthetic(tmp, seed=42)
        yield case_path


@pytest.fixture
def synthetic_case_b():
    """Second synthetic case with slightly different results."""
    with tempfile.TemporaryDirectory() as tmp:
        case_path = _write_full_synthetic(
            tmp, case_name="SPE1_VARIANT", seed=99,
            pressure_decline=12.0,  # Slightly faster decline
            oil_rate_decline=55.0,
        )
        yield case_path


# ═══════════════════════════════════════════════════════════════════════════
# 1. Summary Reader Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSummaryReader:

    def test_reads_wells(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        assert "PROD" in data["wells"]
        assert "INJ" in data["wells"]

    def test_reads_timesteps(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        assert len(data["days"]) == 12
        assert data["days"][0] == pytest.approx(30.0)
        assert data["days"][-1] == pytest.approx(360.0)

    def test_reads_field_oil_rate(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        fopr = data["vectors"]["FOPR"]
        assert len(fopr) == 12
        assert fopr[0] > 0  # Oil being produced

    def test_reads_well_bhp(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        bhp = data["vectors"]["WBHP:PROD"]
        assert len(bhp) == 12
        assert all(v > 0 for v in bhp)

    def test_reads_injection_rate(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        wwir = data["vectors"]["WWIR:INJ"]
        assert all(v > 0 for v in wwir)

    def test_field_pressure_declining(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        fpr = data["vectors"]["FPR"]
        assert fpr[0] > fpr[-1]  # Pressure declining

    def test_cumulative_oil_increasing(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        fopt = data["vectors"]["FOPT"]
        for i in range(1, len(fopt)):
            assert fopt[i] > fopt[i - 1]

    def test_summary_keys_present(self, synthetic_case):
        data = read_summary(synthetic_case + ".SMSPEC")
        expected = {"FOPR", "FWPR", "FPR", "FOPT", "WBHP:PROD", "WBHP:INJ"}
        assert expected.issubset(set(data["keys"]))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Restart Reader Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRestartReader:

    def test_reads_all_steps(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        assert len(steps) == 12

    def test_pressure_present(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        assert "PRESSURE" in steps[0]
        assert len(steps[0]["PRESSURE"]) == 300  # 10×10×3

    def test_saturation_present(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        assert "SWAT" in steps[0]
        assert "SGAS" in steps[0]

    def test_pressure_spatial_variation(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        p = steps[0]["PRESSURE"]
        assert p[0] != pytest.approx(p[-1], abs=1.0)

    def test_pressure_declining_over_time(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        mean_p0 = float(np.mean(steps[0]["PRESSURE"]))
        mean_p11 = float(np.mean(steps[-1]["PRESSURE"]))
        assert mean_p0 > mean_p11

    def test_water_saturation_increasing(self, synthetic_case):
        steps = read_restart(synthetic_case + ".UNRST")
        mean_sw0 = float(np.mean(steps[0]["SWAT"]))
        mean_sw11 = float(np.mean(steps[-1]["SWAT"]))
        assert mean_sw11 > mean_sw0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Full Eclipse Output → UnifiedResult
# ═══════════════════════════════════════════════════════════════════════════


class TestEclipseToUnifiedResult:

    def test_produces_unified_result(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        assert isinstance(result, UnifiedResult)
        assert result.status == SimStatus.COMPLETED

    def test_correct_timestep_count(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        assert len(result.timesteps) == 12

    def test_timestep_days(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        assert result.timesteps[0].time_days == pytest.approx(30.0)
        assert result.timesteps[-1].time_days == pytest.approx(360.0)

    def test_cell_data_present(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        ts = result.timesteps[0]
        assert ts.cells.pressure is not None
        assert len(ts.cells.pressure) == 300

    def test_pressure_converted_to_bar(self, synthetic_case, spe1_request):
        """FIELD units: psia → bar."""
        result = read_eclipse_output(
            synthetic_case, spe1_request, unit_system="FIELD"
        )
        # SPE1 initial pressure ~4800 psia → ~330 bar
        mean_p = sum(result.timesteps[0].cells.pressure) / 300
        assert 250 < mean_p < 400  # Reasonable bar range

    def test_saturation_water_present(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        ts = result.timesteps[0]
        assert ts.cells.saturation_water is not None
        assert all(0 <= v <= 1 for v in ts.cells.saturation_water)

    def test_saturation_oil_computed(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        ts = result.timesteps[0]
        assert ts.cells.saturation_oil is not None
        # So + Sw + Sg ≈ 1 for each cell
        for sw, so, sg in zip(ts.cells.saturation_water,
                               ts.cells.saturation_oil,
                               ts.cells.saturation_gas or [0]*300):
            assert abs(sw + so + sg - 1.0) < 0.01

    def test_wells_present(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        ts = result.timesteps[0]
        well_names = {w.well_name for w in ts.wells}
        assert "PROD" in well_names
        assert "INJ" in well_names

    def test_producer_bhp(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        prod = next(w for w in result.timesteps[0].wells if w.well_name == "PROD")
        assert prod.bhp_bar > 0

    def test_producer_oil_rate(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        prod = next(w for w in result.timesteps[0].wells if w.well_name == "PROD")
        assert prod.oil_rate_m3_day > 0

    def test_injector_water_rate(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        inj = next(w for w in result.timesteps[0].wells if w.well_name == "INJ")
        assert inj.water_rate_m3_day > 0

    def test_metadata(self, synthetic_case, spe1_request):
        result = read_eclipse_output(synthetic_case, spe1_request)
        assert result.metadata.backend == "opm"
        assert result.metadata.grid_cells == 300
        assert result.metadata.converged is True

    def test_handles_smspec_extension(self, synthetic_case, spe1_request):
        """Should work if passed .SMSPEC path."""
        result = read_eclipse_output(synthetic_case + ".SMSPEC", spe1_request)
        assert result.status == SimStatus.COMPLETED

    def test_missing_case_returns_error(self, spe1_request):
        result = read_eclipse_output("/nonexistent/case", spe1_request)
        assert result.status == SimStatus.FAILED


# ═══════════════════════════════════════════════════════════════════════════
# 4. E2E: Two Synthetic Runs → Comparison
# ═══════════════════════════════════════════════════════════════════════════


class TestE2EComparison:
    """The full pipeline: Eclipse binary → Reader → UnifiedResult → Compare."""

    def test_same_run_identical(self, synthetic_case, spe1_request):
        """Same case read twice → perfect match."""
        a = read_eclipse_output(synthetic_case, spe1_request)
        b = read_eclipse_output(synthetic_case, spe1_request)
        report = compare(a, b, "Run A", "Run B")

        assert report.match_quality == "excellent"
        assert report.overall_nrmse == 0.0
        assert report.n_timesteps_compared == 12

    def test_different_runs_comparable(self, synthetic_case, synthetic_case_b, spe1_request):
        """Two different runs → ComparisonReport with metrics."""
        a = read_eclipse_output(synthetic_case, spe1_request, unit_system="FIELD")
        b = read_eclipse_output(synthetic_case_b, spe1_request, unit_system="FIELD")
        report = compare(a, b, "Base", "Variant")

        assert report.n_timesteps_compared > 0
        assert report.overall_nrmse > 0  # Should differ
        assert report.match_quality in ("excellent", "good", "acceptable", "poor")

    def test_comparison_has_cell_metrics(self, synthetic_case, synthetic_case_b, spe1_request):
        a = read_eclipse_output(synthetic_case, spe1_request, unit_system="FIELD")
        b = read_eclipse_output(synthetic_case_b, spe1_request, unit_system="FIELD")
        report = compare(a, b)

        for ts in report.timesteps:
            assert ts.pressure is not None
            assert ts.pressure.count == 300

    def test_comparison_has_well_metrics(self, synthetic_case, synthetic_case_b, spe1_request):
        a = read_eclipse_output(synthetic_case, spe1_request, unit_system="FIELD")
        b = read_eclipse_output(synthetic_case_b, spe1_request, unit_system="FIELD")
        report = compare(a, b)

        for ts in report.timesteps:
            assert len(ts.wells) == 2
            prod_metrics = next(w for w in ts.wells if w.well_name == "PROD")
            assert prod_metrics.bhp_rel_error >= 0

    def test_comparison_report_summary(self, synthetic_case, synthetic_case_b, spe1_request):
        a = read_eclipse_output(synthetic_case, spe1_request, unit_system="FIELD")
        b = read_eclipse_output(synthetic_case_b, spe1_request, unit_system="FIELD")
        report = compare(a, b, "Base Case", "Variant")
        summary = report.summary()

        assert "Base Case vs Variant" in summary["comparison"]
        assert int(summary["timesteps"]) > 0


# ═══════════════════════════════════════════════════════════════════════════
# 5. Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestReaderEdgeCases:

    def test_smspec_only(self):
        """SMSPEC without UNRST → wells but no cell data."""
        with tempfile.TemporaryDirectory() as tmp:
            case = os.path.join(tmp, "NORESTRT")
            _write_synthetic_smspec(case, n_steps=3)
            result = read_eclipse_output(case)
            assert result.status == SimStatus.COMPLETED
            assert len(result.timesteps) == 3
            # Wells should be present
            assert len(result.timesteps[0].wells) > 0
            # Cell data may be empty
            assert result.timesteps[0].cells.pressure is None or \
                   len(result.timesteps[0].cells.pressure) == 0

    def test_unrst_only(self):
        """UNRST without SMSPEC → cell data but no wells."""
        with tempfile.TemporaryDirectory() as tmp:
            case = os.path.join(tmp, "NOSUMMARY")
            _write_synthetic_unrst(case, n_steps=3, n_cells=300)
            result = read_eclipse_output(case)
            assert result.status == SimStatus.COMPLETED
            assert len(result.timesteps) == 3
            assert result.timesteps[0].cells.pressure is not None

    def test_single_timestep(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _write_full_synthetic(tmp, n_steps=1)
            result = read_eclipse_output(case)
            assert len(result.timesteps) == 1

    def test_no_request_provided(self, synthetic_case):
        """Works without a SimRequest."""
        result = read_eclipse_output(synthetic_case)
        assert result.status == SimStatus.COMPLETED
        assert result.metadata.grid_cells == 300
