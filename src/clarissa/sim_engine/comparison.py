"""Comparison Engine — Backend-Agnostic Simulation Result Comparison.

Compares two UnifiedResult objects (from any combination of backends)
and produces a ComparisonReport with statistical metrics, per-cell
deltas, and well-by-well deviation analysis.

Use cases:
  - Cross-validation: OPM vs MRST on same SimRequest
  - Sensitivity analysis: Same backend, different parameters
  - Regression testing: Same deck, different OPM versions

Metrics computed:
  - NRMSE (Normalized Root Mean Square Error)
  - MAE (Mean Absolute Error)
  - Max absolute error + location
  - R² (coefficient of determination)
  - Per-timestep and per-field breakdown

Issue #167 | Epic #161 | ADR-040
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from clarissa.sim_engine.models import (
    SimStatus,
    TimestepResult,
    UnifiedResult,
    WellData,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Result Models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class FieldMetrics:
    """Statistical metrics for a single field (e.g. pressure, Sw)."""

    field_name: str
    nrmse: float = 0.0           # Normalized Root Mean Square Error
    mae: float = 0.0             # Mean Absolute Error
    max_abs_error: float = 0.0   # Maximum absolute difference
    max_error_index: int = -1    # Cell index of max error
    r_squared: float = 1.0       # Coefficient of determination
    mean_a: float = 0.0          # Mean value in result A
    mean_b: float = 0.0          # Mean value in result B
    count: int = 0               # Number of values compared

    @property
    def is_close(self) -> bool:
        """Results are within engineering tolerance (NRMSE < 5%)."""
        return self.nrmse < 0.05

    @property
    def is_excellent(self) -> bool:
        """Results are nearly identical (NRMSE < 1%)."""
        return self.nrmse < 0.01


@dataclass
class WellMetrics:
    """Comparison metrics for a single well."""

    well_name: str
    bhp_diff_bar: float = 0.0
    oil_rate_diff_m3d: float = 0.0
    water_rate_diff_m3d: float = 0.0
    gas_rate_diff_m3d: float = 0.0
    bhp_rel_error: float = 0.0      # |diff| / max(|a|, |b|)
    oil_rate_rel_error: float = 0.0
    water_rate_rel_error: float = 0.0

    @property
    def is_close(self) -> bool:
        return self.bhp_rel_error < 0.05 and self.oil_rate_rel_error < 0.05


@dataclass
class TimestepComparison:
    """Comparison results for a single matched timestep pair."""

    time_days: float
    time_a: float          # Actual time from result A
    time_b: float          # Actual time from result B
    time_mismatch_days: float

    # Cell-level metrics
    pressure: Optional[FieldMetrics] = None
    saturation_water: Optional[FieldMetrics] = None
    saturation_oil: Optional[FieldMetrics] = None
    saturation_gas: Optional[FieldMetrics] = None

    # Well-level metrics
    wells: list[WellMetrics] = field(default_factory=list)

    @property
    def all_fields(self) -> list[FieldMetrics]:
        return [f for f in [self.pressure, self.saturation_water,
                            self.saturation_oil, self.saturation_gas] if f]

    @property
    def worst_nrmse(self) -> float:
        fields = self.all_fields
        return max((f.nrmse for f in fields), default=0.0)

    @property
    def is_close(self) -> bool:
        return all(f.is_close for f in self.all_fields)


@dataclass
class ComparisonReport:
    """Complete comparison report between two simulation results."""

    # Source identification
    label_a: str
    label_b: str
    backend_a: str
    backend_b: str

    # Overall verdict
    overall_nrmse: float = 0.0
    overall_mae: float = 0.0
    overall_max_error: float = 0.0
    match_quality: str = "unknown"  # "excellent", "good", "acceptable", "poor"

    # Grid compatibility
    grid_compatible: bool = True
    grid_cells_a: int = 0
    grid_cells_b: int = 0

    # Per-timestep breakdown
    timesteps: list[TimestepComparison] = field(default_factory=list)

    # Aggregated field metrics (over all timesteps)
    aggregate_pressure: Optional[FieldMetrics] = None
    aggregate_saturation_water: Optional[FieldMetrics] = None
    aggregate_saturation_oil: Optional[FieldMetrics] = None

    # Metadata
    warnings: list[str] = field(default_factory=list)

    @property
    def n_timesteps_compared(self) -> int:
        return len(self.timesteps)

    @property
    def is_cross_backend(self) -> bool:
        return self.backend_a != self.backend_b

    def summary(self) -> dict[str, Any]:
        """Quick summary for logging."""
        return {
            "comparison": f"{self.label_a} vs {self.label_b}",
            "backends": f"{self.backend_a} vs {self.backend_b}",
            "timesteps": self.n_timesteps_compared,
            "overall_nrmse": f"{self.overall_nrmse:.4f}",
            "quality": self.match_quality,
            "grid_compatible": self.grid_compatible,
            "warnings": len(self.warnings),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Core Comparison Functions
# ═══════════════════════════════════════════════════════════════════════════


def compare(
    result_a: UnifiedResult,
    result_b: UnifiedResult,
    label_a: str = "A",
    label_b: str = "B",
    time_tolerance_days: float = 1.0,
) -> ComparisonReport:
    """Compare two UnifiedResult objects.

    Args:
        result_a: First simulation result.
        result_b: Second simulation result.
        label_a: Label for result A (e.g. "OPM", "baseline").
        label_b: Label for result B (e.g. "MRST", "modified").
        time_tolerance_days: Maximum timestep mismatch allowed.

    Returns:
        ComparisonReport with detailed metrics.
    """
    report = ComparisonReport(
        label_a=label_a,
        label_b=label_b,
        backend_a=result_a.metadata.backend,
        backend_b=result_b.metadata.backend,
        grid_cells_a=result_a.metadata.grid_cells,
        grid_cells_b=result_b.metadata.grid_cells,
    )

    # Pre-flight checks
    if result_a.status != SimStatus.COMPLETED:
        report.warnings.append(f"{label_a} status: {result_a.status.value}")
        report.match_quality = "invalid"
        return report

    if result_b.status != SimStatus.COMPLETED:
        report.warnings.append(f"{label_b} status: {result_b.status.value}")
        report.match_quality = "invalid"
        return report

    if not result_a.timesteps or not result_b.timesteps:
        report.warnings.append("One or both results have no timesteps")
        report.match_quality = "invalid"
        return report

    # Grid compatibility check
    cells_a = result_a.metadata.grid_cells
    cells_b = result_b.metadata.grid_cells
    if cells_a != cells_b:
        report.grid_compatible = False
        report.warnings.append(
            f"Grid mismatch: {label_a}={cells_a} cells, {label_b}={cells_b} cells. "
            "Cell-level comparison disabled."
        )

    # Match timesteps
    matched = _match_timesteps(
        result_a.timesteps, result_b.timesteps, time_tolerance_days
    )

    if not matched:
        report.warnings.append("No timesteps matched within tolerance")
        report.match_quality = "invalid"
        return report

    # Compare each matched pair
    all_pressure_nrmse = []
    all_sw_nrmse = []
    all_so_nrmse = []

    for ts_a, ts_b in matched:
        ts_comp = _compare_timestep(
            ts_a, ts_b,
            grid_compatible=report.grid_compatible,
        )
        report.timesteps.append(ts_comp)

        if ts_comp.pressure:
            all_pressure_nrmse.append(ts_comp.pressure.nrmse)
        if ts_comp.saturation_water:
            all_sw_nrmse.append(ts_comp.saturation_water.nrmse)
        if ts_comp.saturation_oil:
            all_so_nrmse.append(ts_comp.saturation_oil.nrmse)

    # Aggregate metrics
    if all_pressure_nrmse:
        report.aggregate_pressure = FieldMetrics(
            field_name="pressure_aggregate",
            nrmse=_rms(all_pressure_nrmse),
            mae=sum(all_pressure_nrmse) / len(all_pressure_nrmse),
            max_abs_error=max(all_pressure_nrmse),
        )
    if all_sw_nrmse:
        report.aggregate_saturation_water = FieldMetrics(
            field_name="sw_aggregate",
            nrmse=_rms(all_sw_nrmse),
            mae=sum(all_sw_nrmse) / len(all_sw_nrmse),
            max_abs_error=max(all_sw_nrmse),
        )
    if all_so_nrmse:
        report.aggregate_saturation_oil = FieldMetrics(
            field_name="so_aggregate",
            nrmse=_rms(all_so_nrmse),
            mae=sum(all_so_nrmse) / len(all_so_nrmse),
            max_abs_error=max(all_so_nrmse),
        )

    # Overall NRMSE — weighted average across fields
    all_nrmse = all_pressure_nrmse + all_sw_nrmse + all_so_nrmse
    report.overall_nrmse = _rms(all_nrmse) if all_nrmse else 0.0
    report.overall_mae = sum(all_nrmse) / len(all_nrmse) if all_nrmse else 0.0
    report.overall_max_error = max(all_nrmse) if all_nrmse else 0.0

    # Quality classification
    report.match_quality = _classify_quality(report.overall_nrmse)

    return report


# ═══════════════════════════════════════════════════════════════════════════
# Internal Functions
# ═══════════════════════════════════════════════════════════════════════════


def _match_timesteps(
    ts_a: list[TimestepResult],
    ts_b: list[TimestepResult],
    tolerance: float,
) -> list[tuple[TimestepResult, TimestepResult]]:
    """Match timesteps between two results by closest time.

    Uses greedy nearest-neighbor matching. Each timestep in B is matched
    to the closest unmatched timestep in A within tolerance.
    """
    matched = []
    used_b = set()

    for a in ts_a:
        best_idx = -1
        best_dist = float("inf")

        for j, b in enumerate(ts_b):
            if j in used_b:
                continue
            dist = abs(a.time_days - b.time_days)
            if dist < best_dist and dist <= tolerance:
                best_dist = dist
                best_idx = j

        if best_idx >= 0:
            matched.append((a, ts_b[best_idx]))
            used_b.add(best_idx)

    return matched


def _compare_timestep(
    ts_a: TimestepResult,
    ts_b: TimestepResult,
    grid_compatible: bool,
) -> TimestepComparison:
    """Compare a single matched timestep pair."""
    comp = TimestepComparison(
        time_days=(ts_a.time_days + ts_b.time_days) / 2,
        time_a=ts_a.time_days,
        time_b=ts_b.time_days,
        time_mismatch_days=abs(ts_a.time_days - ts_b.time_days),
    )

    # Cell-level comparison (only if grids match)
    if grid_compatible:
        if ts_a.cells.pressure and ts_b.cells.pressure:
            comp.pressure = _compare_arrays(
                ts_a.cells.pressure, ts_b.cells.pressure, "pressure"
            )

        if ts_a.cells.saturation_water and ts_b.cells.saturation_water:
            comp.saturation_water = _compare_arrays(
                ts_a.cells.saturation_water, ts_b.cells.saturation_water,
                "saturation_water",
            )

        if ts_a.cells.saturation_oil and ts_b.cells.saturation_oil:
            comp.saturation_oil = _compare_arrays(
                ts_a.cells.saturation_oil, ts_b.cells.saturation_oil,
                "saturation_oil",
            )

        if ts_a.cells.saturation_gas and ts_b.cells.saturation_gas:
            comp.saturation_gas = _compare_arrays(
                ts_a.cells.saturation_gas, ts_b.cells.saturation_gas,
                "saturation_gas",
            )

    # Well-level comparison
    wells_b_map = {w.well_name: w for w in ts_b.wells}
    for wa in ts_a.wells:
        wb = wells_b_map.get(wa.well_name)
        if wb:
            comp.wells.append(_compare_wells(wa, wb))

    return comp


def _compare_arrays(
    a: list[float],
    b: list[float],
    field_name: str,
) -> FieldMetrics:
    """Compare two float arrays element-wise."""
    n = min(len(a), len(b))
    if n == 0:
        return FieldMetrics(field_name=field_name, count=0)

    sum_sq_diff = 0.0
    sum_abs_diff = 0.0
    max_diff = 0.0
    max_idx = 0
    sum_a = 0.0
    sum_b = 0.0
    sum_sq_a = 0.0
    mean_b_accum = 0.0

    for i in range(n):
        diff = a[i] - b[i]
        abs_diff = abs(diff)
        sum_sq_diff += diff * diff
        sum_abs_diff += abs_diff
        sum_a += a[i]
        sum_b += b[i]
        sum_sq_a += a[i] * a[i]

        if abs_diff > max_diff:
            max_diff = abs_diff
            max_idx = i

    mean_a = sum_a / n
    mean_b = sum_b / n
    mse = sum_sq_diff / n
    rmse = math.sqrt(mse)

    # NRMSE: normalize by range of reference values
    a_min = min(a[:n])
    a_max = max(a[:n])
    data_range = a_max - a_min
    nrmse = rmse / data_range if data_range > 1e-10 else (0.0 if rmse < 1e-10 else 1.0)

    # R²: coefficient of determination
    ss_res = sum_sq_diff
    ss_tot = sum((a[i] - mean_a) ** 2 for i in range(n))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-10 else (1.0 if ss_res < 1e-10 else 0.0)

    return FieldMetrics(
        field_name=field_name,
        nrmse=nrmse,
        mae=sum_abs_diff / n,
        max_abs_error=max_diff,
        max_error_index=max_idx,
        r_squared=max(0.0, r_squared),  # Clamp negative R²
        mean_a=mean_a,
        mean_b=mean_b,
        count=n,
    )


def _compare_wells(wa: WellData, wb: WellData) -> WellMetrics:
    """Compare well data between two results."""
    return WellMetrics(
        well_name=wa.well_name,
        bhp_diff_bar=wa.bhp_bar - wb.bhp_bar,
        oil_rate_diff_m3d=wa.oil_rate_m3_day - wb.oil_rate_m3_day,
        water_rate_diff_m3d=wa.water_rate_m3_day - wb.water_rate_m3_day,
        gas_rate_diff_m3d=wa.gas_rate_m3_day - wb.gas_rate_m3_day,
        bhp_rel_error=_rel_error(wa.bhp_bar, wb.bhp_bar),
        oil_rate_rel_error=_rel_error(wa.oil_rate_m3_day, wb.oil_rate_m3_day),
        water_rate_rel_error=_rel_error(wa.water_rate_m3_day, wb.water_rate_m3_day),
    )


def _rel_error(a: float, b: float) -> float:
    """Relative error: |a - b| / max(|a|, |b|)."""
    denom = max(abs(a), abs(b))
    if denom < 1e-10:
        return 0.0
    return abs(a - b) / denom


def _rms(values: list[float]) -> float:
    """Root mean square of a list."""
    if not values:
        return 0.0
    return math.sqrt(sum(v * v for v in values) / len(values))


def _classify_quality(nrmse: float) -> str:
    """Classify comparison quality from NRMSE."""
    if nrmse < 0.01:
        return "excellent"
    elif nrmse < 0.05:
        return "good"
    elif nrmse < 0.10:
        return "acceptable"
    else:
        return "poor"
