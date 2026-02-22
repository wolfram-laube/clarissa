"""Tests for Comparison Engine (Issue #167).

Covers:
1. Identical results → perfect match (NRMSE=0, R²=1)
2. Known differences → correct metrics
3. Cross-backend comparison (OPM vs MRST)
4. Grid mismatch handling
5. Timestep matching with tolerance
6. Well-level comparison
7. Quality classification
8. Edge cases (empty, failed, single timestep)
9. Real-data shaped tests (SPE1-like dimensions)

Issue #167 | Epic #161 | ADR-040
"""
from __future__ import annotations

import math
import random
from typing import Optional

import pytest

from clarissa.sim_engine.comparison import (
    ComparisonReport,
    FieldMetrics,
    TimestepComparison,
    WellMetrics,
    compare,
    _compare_arrays,
    _compare_wells,
    _match_timesteps,
    _classify_quality,
    _rel_error,
)
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


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


def _make_request(nx=10, ny=10, nz=3) -> SimRequest:
    """Minimal SimRequest for testing."""
    return SimRequest(
        grid=GridParams(nx=nx, ny=ny, nz=nz),
        wells=[
            WellConfig(name="INJ", well_type=WellType.INJECTOR,
                       i=0, j=0, rate_m3_day=100, phases=[Phase.WATER]),
            WellConfig(name="PROD", well_type=WellType.PRODUCER,
                       i=nx - 1, j=ny - 1, bhp_bar=150, phases=[Phase.OIL]),
        ],
        timesteps_days=[30, 90, 365],
    )


def _make_result(
    backend: str = "opm",
    n_cells: int = 300,
    timestep_days: Optional[list[float]] = None,
    pressure_base: float = 200.0,
    pressure_noise: float = 0.0,
    sw_base: float = 0.2,
    sw_noise: float = 0.0,
    status: SimStatus = SimStatus.COMPLETED,
    seed: int = 42,
) -> UnifiedResult:
    """Create a synthetic UnifiedResult for testing.

    Args:
        pressure_noise: Std dev of Gaussian noise added to pressure.
        sw_noise: Std dev of noise added to water saturation.
    """
    rng = random.Random(seed)
    if timestep_days is None:
        timestep_days = [30.0, 90.0, 365.0]

    timesteps = []
    for t in timestep_days:
        # Pressure decreases with time (drawdown) + spatial gradient
        p_mean = pressure_base - t * 0.01
        pressure = [
            p_mean
            + (i / n_cells) * 20.0  # spatial gradient: 0..20 bar across grid
            + (rng.gauss(0, pressure_noise) if pressure_noise > 0 else 0)
            for i in range(n_cells)
        ]
        sw = [
            min(1.0, max(0.0,
                sw_base
                + (i / n_cells) * 0.1   # spatial gradient: 0..0.1 across grid
                + t * 0.0001
                + (rng.gauss(0, sw_noise) if sw_noise > 0 else 0)
            ))
            for i in range(n_cells)
        ]
        so = [1.0 - s for s in sw]

        wells = [
            WellData(
                well_name="INJ",
                oil_rate_m3_day=0,
                water_rate_m3_day=100.0,
                bhp_bar=220.0 - t * 0.01,
            ),
            WellData(
                well_name="PROD",
                oil_rate_m3_day=80.0 - t * 0.05,
                water_rate_m3_day=10.0 + t * 0.02,
                bhp_bar=150.0,
            ),
        ]

        timesteps.append(TimestepResult(
            time_days=t,
            cells=CellData(
                pressure=pressure,
                saturation_water=sw,
                saturation_oil=so,
            ),
            wells=wells,
        ))

    return UnifiedResult(
        job_id=f"{backend}-test",
        title="Test Result",
        status=status,
        request=_make_request(),
        timesteps=timesteps,
        metadata=SimMetadata(
            backend=backend,
            backend_version="test",
            grid_cells=n_cells,
            wall_time_seconds=5.0,
            converged=True,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Identical Results
# ═══════════════════════════════════════════════════════════════════════════


class TestIdenticalResults:
    """Two identical results should produce perfect comparison."""

    def test_perfect_match_nrmse(self):
        a = _make_result(backend="opm", seed=42)
        b = _make_result(backend="opm", seed=42)
        report = compare(a, b, "A", "B")

        assert report.overall_nrmse == 0.0
        assert report.match_quality == "excellent"

    def test_perfect_match_r_squared(self):
        a = _make_result(seed=42)
        b = _make_result(seed=42)
        report = compare(a, b)

        for ts in report.timesteps:
            if ts.pressure:
                assert ts.pressure.r_squared == 1.0
            if ts.saturation_water:
                assert ts.saturation_water.r_squared == 1.0

    def test_perfect_match_mae(self):
        a = _make_result(seed=42)
        b = _make_result(seed=42)
        report = compare(a, b)
        assert report.overall_mae == 0.0

    def test_perfect_match_max_error(self):
        a = _make_result(seed=42)
        b = _make_result(seed=42)
        report = compare(a, b)
        assert report.overall_max_error == 0.0

    def test_all_timesteps_matched(self):
        a = _make_result(seed=42)
        b = _make_result(seed=42)
        report = compare(a, b)
        assert report.n_timesteps_compared == 3

    def test_wells_compared(self):
        a = _make_result(seed=42)
        b = _make_result(seed=42)
        report = compare(a, b)
        for ts in report.timesteps:
            assert len(ts.wells) == 2
            for wm in ts.wells:
                assert wm.bhp_diff_bar == 0.0
                assert wm.oil_rate_diff_m3d == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Known Differences
# ═══════════════════════════════════════════════════════════════════════════


class TestKnownDifferences:
    """Results with controlled noise → predictable metrics."""

    def test_small_noise_good_quality(self):
        """Small noise → still 'good' or 'excellent'."""
        a = _make_result(pressure_base=200, pressure_noise=0, seed=1)
        b = _make_result(pressure_base=200, pressure_noise=0.1, seed=2)
        report = compare(a, b)
        assert report.match_quality in ("excellent", "good")

    def test_large_noise_poor_quality(self):
        """Large noise → 'poor' quality."""
        a = _make_result(pressure_base=200, pressure_noise=0, seed=1)
        b = _make_result(pressure_base=200, pressure_noise=50, seed=2)
        report = compare(a, b)
        assert report.match_quality in ("acceptable", "poor")

    def test_systematic_offset(self):
        """Constant pressure offset → nonzero MAE, detectable."""
        a = _make_result(pressure_base=200, seed=42)
        b = _make_result(pressure_base=205, seed=42)  # 5 bar offset
        report = compare(a, b)

        assert report.overall_nrmse > 0
        for ts in report.timesteps:
            if ts.pressure:
                assert abs(ts.pressure.mae - 5.0) < 0.1

    def test_nrmse_increases_with_noise(self):
        """More noise → higher NRMSE."""
        a = _make_result(pressure_noise=0, seed=1)
        b_low = _make_result(pressure_noise=1.0, seed=2)
        b_high = _make_result(pressure_noise=10.0, seed=3)

        r_low = compare(a, b_low)
        r_high = compare(a, b_high)

        assert r_high.overall_nrmse > r_low.overall_nrmse

    def test_different_saturation(self):
        """Different Sw base → detected."""
        a = _make_result(sw_base=0.2, seed=42)
        b = _make_result(sw_base=0.3, seed=42)
        report = compare(a, b)

        for ts in report.timesteps:
            if ts.saturation_water:
                assert ts.saturation_water.mae > 0.05


# ═══════════════════════════════════════════════════════════════════════════
# 3. Cross-Backend Comparison
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossBackend:
    """OPM vs MRST comparison scenarios."""

    def test_is_cross_backend(self):
        a = _make_result(backend="opm")
        b = _make_result(backend="mrst")
        report = compare(a, b, "OPM", "MRST")
        assert report.is_cross_backend is True
        assert report.backend_a == "opm"
        assert report.backend_b == "mrst"

    def test_same_backend_not_cross(self):
        a = _make_result(backend="opm")
        b = _make_result(backend="opm")
        report = compare(a, b)
        assert report.is_cross_backend is False

    def test_labels_preserved(self):
        a = _make_result(backend="opm")
        b = _make_result(backend="mrst")
        report = compare(a, b, "OPM Flow 2025.10", "MRST via Octave 8.4")
        assert report.label_a == "OPM Flow 2025.10"
        assert report.label_b == "MRST via Octave 8.4"

    def test_cross_backend_with_noise(self):
        """Cross-backend with small numerical differences → good quality."""
        a = _make_result(backend="opm", pressure_noise=0.5, seed=1)
        b = _make_result(backend="mrst", pressure_noise=0.5, seed=2)
        report = compare(a, b, "OPM", "MRST")
        # Both have noise, but similar — should be reasonable
        assert report.match_quality in ("excellent", "good", "acceptable")


# ═══════════════════════════════════════════════════════════════════════════
# 4. Grid Mismatch
# ═══════════════════════════════════════════════════════════════════════════


class TestGridMismatch:
    """Different grid sizes → cell comparison disabled."""

    def test_grid_mismatch_detected(self):
        a = _make_result(n_cells=300)
        b = _make_result(n_cells=500)
        report = compare(a, b)
        assert report.grid_compatible is False
        assert any("mismatch" in w.lower() for w in report.warnings)

    def test_grid_mismatch_no_cell_metrics(self):
        a = _make_result(n_cells=300)
        b = _make_result(n_cells=500)
        report = compare(a, b)
        for ts in report.timesteps:
            assert ts.pressure is None
            assert ts.saturation_water is None

    def test_grid_mismatch_wells_still_compared(self):
        """Wells can still be compared even if grids differ."""
        a = _make_result(n_cells=300)
        b = _make_result(n_cells=500)
        report = compare(a, b)
        for ts in report.timesteps:
            assert len(ts.wells) == 2

    def test_grid_cells_recorded(self):
        a = _make_result(n_cells=300)
        b = _make_result(n_cells=9000)
        report = compare(a, b)
        assert report.grid_cells_a == 300
        assert report.grid_cells_b == 9000


# ═══════════════════════════════════════════════════════════════════════════
# 5. Timestep Matching
# ═══════════════════════════════════════════════════════════════════════════


class TestTimestepMatching:
    """Timestep pairing logic."""

    def test_exact_match(self):
        ts_a = [TimestepResult(time_days=30), TimestepResult(time_days=90)]
        ts_b = [TimestepResult(time_days=30), TimestepResult(time_days=90)]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 2

    def test_close_match(self):
        """Slightly different times within tolerance."""
        ts_a = [TimestepResult(time_days=30.0)]
        ts_b = [TimestepResult(time_days=30.5)]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 1

    def test_beyond_tolerance(self):
        ts_a = [TimestepResult(time_days=30.0)]
        ts_b = [TimestepResult(time_days=35.0)]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 0

    def test_partial_match(self):
        """Only some timesteps match."""
        ts_a = [TimestepResult(time_days=30), TimestepResult(time_days=90),
                TimestepResult(time_days=365)]
        ts_b = [TimestepResult(time_days=30), TimestepResult(time_days=180)]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 1  # Only day 30

    def test_different_count(self):
        """A has more timesteps than B."""
        ts_a = [TimestepResult(time_days=t) for t in [30, 60, 90, 180, 365]]
        ts_b = [TimestepResult(time_days=t) for t in [30, 90, 365]]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 3

    def test_no_double_matching(self):
        """Each B timestep used at most once."""
        ts_a = [TimestepResult(time_days=30), TimestepResult(time_days=30.5)]
        ts_b = [TimestepResult(time_days=30)]
        matched = _match_timesteps(ts_a, ts_b, tolerance=1.0)
        assert len(matched) == 1

    def test_time_mismatch_recorded(self):
        a = _make_result(timestep_days=[30.0, 90.0])
        b = _make_result(timestep_days=[30.5, 90.2])
        report = compare(a, b, time_tolerance_days=1.0)
        assert report.timesteps[0].time_mismatch_days == pytest.approx(0.5, abs=0.01)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Array-Level Metrics
# ═══════════════════════════════════════════════════════════════════════════


class TestArrayMetrics:
    """Direct tests on _compare_arrays."""

    def test_identical_arrays(self):
        a = [100.0, 200.0, 300.0]
        m = _compare_arrays(a, a, "test")
        assert m.nrmse == 0.0
        assert m.mae == 0.0
        assert m.r_squared == 1.0

    def test_constant_offset(self):
        a = [100.0, 200.0, 300.0]
        b = [110.0, 210.0, 310.0]
        m = _compare_arrays(a, b, "test")
        assert m.mae == 10.0
        assert m.max_abs_error == 10.0
        assert m.r_squared == pytest.approx(1.0, abs=0.02)  # Near-perfect linear correlation

    def test_single_outlier(self):
        a = [100.0, 100.0, 100.0, 100.0, 200.0]
        b = [100.0, 100.0, 100.0, 100.0, 100.0]
        m = _compare_arrays(a, b, "test")
        assert m.max_abs_error == 100.0
        assert m.max_error_index == 4

    def test_empty_arrays(self):
        m = _compare_arrays([], [], "test")
        assert m.count == 0

    def test_different_lengths(self):
        """Uses min(len(a), len(b))."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.0, 2.0, 3.0]
        m = _compare_arrays(a, b, "test")
        assert m.count == 3

    def test_nrmse_normalized_by_range(self):
        """NRMSE = RMSE / (max - min)."""
        a = [0.0, 100.0]
        b = [10.0, 90.0]
        m = _compare_arrays(a, b, "test")
        # RMSE = sqrt((100+100)/2) = 10, range = 100, NRMSE = 0.1
        assert m.nrmse == pytest.approx(0.1, abs=0.001)

    def test_constant_values_zero_range(self):
        """All values identical → NRMSE should be 0 (not division by zero)."""
        a = [5.0, 5.0, 5.0]
        b = [5.0, 5.0, 5.0]
        m = _compare_arrays(a, b, "test")
        assert m.nrmse == 0.0

    def test_mean_values(self):
        a = [10.0, 20.0, 30.0]
        b = [11.0, 21.0, 31.0]
        m = _compare_arrays(a, b, "test")
        assert m.mean_a == pytest.approx(20.0)
        assert m.mean_b == pytest.approx(21.0)


# ═══════════════════════════════════════════════════════════════════════════
# 7. Well Comparison
# ═══════════════════════════════════════════════════════════════════════════


class TestWellComparison:

    def test_identical_wells(self):
        w = WellData(well_name="PROD", bhp_bar=150, oil_rate_m3_day=80)
        m = _compare_wells(w, w)
        assert m.bhp_diff_bar == 0.0
        assert m.oil_rate_diff_m3d == 0.0
        assert m.bhp_rel_error == 0.0

    def test_bhp_difference(self):
        wa = WellData(well_name="PROD", bhp_bar=150, oil_rate_m3_day=80)
        wb = WellData(well_name="PROD", bhp_bar=145, oil_rate_m3_day=80)
        m = _compare_wells(wa, wb)
        assert m.bhp_diff_bar == 5.0
        assert m.bhp_rel_error == pytest.approx(5.0 / 150.0, abs=0.001)

    def test_rate_difference(self):
        wa = WellData(well_name="PROD", oil_rate_m3_day=100)
        wb = WellData(well_name="PROD", oil_rate_m3_day=90)
        m = _compare_wells(wa, wb)
        assert m.oil_rate_diff_m3d == 10.0
        assert m.oil_rate_rel_error == pytest.approx(0.1, abs=0.001)

    def test_zero_rate_no_div_by_zero(self):
        wa = WellData(well_name="INJ", oil_rate_m3_day=0)
        wb = WellData(well_name="INJ", oil_rate_m3_day=0)
        m = _compare_wells(wa, wb)
        assert m.oil_rate_rel_error == 0.0

    def test_well_is_close(self):
        wa = WellData(well_name="PROD", bhp_bar=150, oil_rate_m3_day=80)
        wb = WellData(well_name="PROD", bhp_bar=149, oil_rate_m3_day=79)
        m = _compare_wells(wa, wb)
        assert m.is_close is True

    def test_well_not_close(self):
        wa = WellData(well_name="PROD", bhp_bar=150, oil_rate_m3_day=80)
        wb = WellData(well_name="PROD", bhp_bar=100, oil_rate_m3_day=80)
        m = _compare_wells(wa, wb)
        assert m.is_close is False


# ═══════════════════════════════════════════════════════════════════════════
# 8. Quality Classification
# ═══════════════════════════════════════════════════════════════════════════


class TestQualityClassification:

    def test_excellent(self):
        assert _classify_quality(0.005) == "excellent"
        assert _classify_quality(0.0) == "excellent"

    def test_good(self):
        assert _classify_quality(0.02) == "good"
        assert _classify_quality(0.049) == "good"

    def test_acceptable(self):
        assert _classify_quality(0.07) == "acceptable"

    def test_poor(self):
        assert _classify_quality(0.15) == "poor"
        assert _classify_quality(1.0) == "poor"

    def test_field_metrics_is_close(self):
        f = FieldMetrics(field_name="test", nrmse=0.03)
        assert f.is_close is True
        assert f.is_excellent is False

    def test_field_metrics_is_excellent(self):
        f = FieldMetrics(field_name="test", nrmse=0.005)
        assert f.is_excellent is True
        assert f.is_close is True

    def test_timestep_is_close(self):
        ts = TimestepComparison(
            time_days=30, time_a=30, time_b=30, time_mismatch_days=0,
            pressure=FieldMetrics(field_name="p", nrmse=0.01),
            saturation_water=FieldMetrics(field_name="sw", nrmse=0.02),
        )
        assert ts.is_close is True
        assert ts.worst_nrmse == 0.02


# ═══════════════════════════════════════════════════════════════════════════
# 9. Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:

    def test_failed_result_a(self):
        a = _make_result(status=SimStatus.FAILED)
        b = _make_result()
        report = compare(a, b)
        assert report.match_quality == "invalid"
        assert any("failed" in w.lower() for w in report.warnings)

    def test_failed_result_b(self):
        a = _make_result()
        b = _make_result(status=SimStatus.FAILED)
        report = compare(a, b)
        assert report.match_quality == "invalid"

    def test_empty_timesteps(self):
        a = _make_result()
        a.timesteps = []
        b = _make_result()
        report = compare(a, b)
        assert report.match_quality == "invalid"

    def test_single_timestep(self):
        a = _make_result(timestep_days=[30.0])
        b = _make_result(timestep_days=[30.0])
        report = compare(a, b)
        assert report.n_timesteps_compared == 1

    def test_no_matching_timesteps(self):
        a = _make_result(timestep_days=[30.0])
        b = _make_result(timestep_days=[365.0])
        report = compare(a, b, time_tolerance_days=1.0)
        assert report.n_timesteps_compared == 0
        assert report.match_quality == "invalid"

    def test_report_summary(self):
        a = _make_result(backend="opm", seed=42)
        b = _make_result(backend="mrst", seed=42)
        report = compare(a, b, "OPM", "MRST")
        summary = report.summary()
        assert "OPM vs MRST" in summary["comparison"]
        assert "opm vs mrst" in summary["backends"]
        assert summary["timesteps"] == 3

    def test_rel_error_helper(self):
        assert _rel_error(100, 90) == pytest.approx(0.1)
        assert _rel_error(0, 0) == 0.0
        assert _rel_error(100, 100) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 10. SPE1-Shaped Comparison
# ═══════════════════════════════════════════════════════════════════════════


class TestSPE1ShapedComparison:
    """Realistic comparison with SPE1 dimensions (300 cells, 2 wells, 120 steps)."""

    @pytest.fixture
    def spe1_opm(self) -> UnifiedResult:
        """Simulated OPM result with SPE1 dimensions."""
        return _make_result(
            backend="opm",
            n_cells=300,
            timestep_days=[float(30 * i) for i in range(1, 13)],
            pressure_base=330.0,  # ~4800 psia in bar
            pressure_noise=0.5,
            sw_base=0.12,
            seed=100,
        )

    @pytest.fixture
    def spe1_mrst(self) -> UnifiedResult:
        """Simulated MRST result — same physics, slight numerical diff."""
        return _make_result(
            backend="mrst",
            n_cells=300,
            timestep_days=[float(30 * i) for i in range(1, 13)],
            pressure_base=330.0,
            pressure_noise=0.8,  # Slightly more noise (different solver)
            sw_base=0.12,
            seed=200,
        )

    def test_spe1_cross_validation(self, spe1_opm, spe1_mrst):
        report = compare(spe1_opm, spe1_mrst, "OPM SPE1", "MRST SPE1")

        assert report.is_cross_backend
        assert report.grid_compatible
        assert report.n_timesteps_compared == 12
        assert report.match_quality in ("excellent", "good", "acceptable")

    def test_spe1_aggregate_pressure(self, spe1_opm, spe1_mrst):
        report = compare(spe1_opm, spe1_mrst)
        assert report.aggregate_pressure is not None
        assert report.aggregate_pressure.nrmse >= 0

    def test_spe1_per_timestep_trend(self, spe1_opm, spe1_mrst):
        """Later timesteps may have larger differences (error accumulation)."""
        report = compare(spe1_opm, spe1_mrst)
        # Just verify all timesteps have metrics
        for ts in report.timesteps:
            assert ts.pressure is not None
            assert ts.saturation_water is not None
            assert ts.pressure.count == 300

    def test_spe1_well_comparison(self, spe1_opm, spe1_mrst):
        report = compare(spe1_opm, spe1_mrst)
        for ts in report.timesteps:
            assert len(ts.wells) == 2
            well_names = {wm.well_name for wm in ts.wells}
            assert "INJ" in well_names
            assert "PROD" in well_names
