"""Eclipse Output Reader — .SMSPEC/.UNRST → UnifiedResult.

Reads OPM Flow (and Eclipse) binary output files and produces
CLARISSA's UnifiedResult. Uses resdata for summary data and
resfo for restart (cell-level) data.

Dependencies:
  - resdata: Summary time-series (well rates, BHP, field totals)
  - resfo: Restart binary records (per-cell pressure, saturation)

Output file types:
  .SMSPEC/.UNSMRY — Summary specification + time-series data
  .UNRST          — Unified restart (per-cell properties per report step)
  .EGRID          — Grid geometry (optional, for cell-count verification)

Issue #108 | Epic #161 | ADR-040
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np

from clarissa.sim_engine.models import (
    CellData,
    SimMetadata,
    SimRequest,
    SimStatus,
    TimestepResult,
    UnifiedResult,
    WellData,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Unit Conversion (FIELD → SI)
# ═══════════════════════════════════════════════════════════════════════════

# OPM outputs in the unit system declared in the deck.
# FIELD units: pressure in psia, rates in STB/day or Mscf/day
# METRIC units: pressure in barsa, rates in sm³/day

def _psi_to_bar(psi: float) -> float:
    return psi * 0.0689476

def _stbd_to_m3d(stbd: float) -> float:
    return stbd * 0.158987

def _mscfd_to_m3d(mscfd: float) -> float:
    return mscfd * 28.3168


# ═══════════════════════════════════════════════════════════════════════════
# Summary Reader (.SMSPEC/.UNSMRY)
# ═══════════════════════════════════════════════════════════════════════════


def read_summary(smspec_path: str) -> dict[str, Any]:
    """Read Eclipse summary file into structured dict.

    Returns:
        {
            "wells": ["PROD", "INJ", ...],
            "days": [30.0, 60.0, ...],
            "dates": [datetime, ...],
            "keys": ["FOPR", "WBHP:PROD", ...],
            "vectors": {"FOPR": np.array, "WBHP:PROD": np.array, ...},
            "unit_system": "FIELD" | "METRIC" | "LAB",
        }
    """
    from resdata.summary import Summary

    s = Summary(smspec_path)

    vectors = {}
    for key in s.keys():
        try:
            vectors[key] = s.numpy_vector(key)
        except Exception as e:
            logger.warning(f"Failed to read summary key {key}: {e}")

    # Detect unit system
    unit_system = "FIELD"  # default
    try:
        us = s.unit_system
        if us is not None:
            unit_system = str(us).upper()
            if "METRIC" in unit_system:
                unit_system = "METRIC"
            elif "FIELD" in unit_system:
                unit_system = "FIELD"
    except Exception:
        pass

    return {
        "wells": list(s.wells()),
        "days": list(s.days),
        "dates": list(s.dates),
        "keys": list(s.keys()),
        "vectors": vectors,
        "unit_system": unit_system,
        "length": len(s),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Restart Reader (.UNRST)
# ═══════════════════════════════════════════════════════════════════════════


def read_restart(unrst_path: str) -> list[dict[str, np.ndarray]]:
    """Read Eclipse restart file into list of per-step arrays.

    Returns:
        [
            {"PRESSURE": np.array, "SWAT": np.array, "SGAS": np.array, ...},
            ...
        ]
    """
    import resfo

    records = list(resfo.read(unrst_path))

    # Group records by SEQNUM
    steps: list[dict[str, np.ndarray]] = []
    current_step: dict[str, np.ndarray] = {}

    for name, data in records:
        kw = name.strip()
        if kw == "SEQNUM":
            if current_step:
                steps.append(current_step)
            current_step = {"SEQNUM": data}
        elif kw in ("PRESSURE", "SWAT", "SGAS", "SOIL", "RS", "RV",
                     "INTEHEAD", "DOUBHEAD", "LOGIHEAD"):
            current_step[kw] = data

    # Don't forget last step
    if current_step:
        steps.append(current_step)

    return steps


# ═══════════════════════════════════════════════════════════════════════════
# Main Reader: Eclipse Output → UnifiedResult
# ═══════════════════════════════════════════════════════════════════════════


def read_eclipse_output(
    case_path: str,
    request: Optional[SimRequest] = None,
    unit_system: Optional[str] = None,
) -> UnifiedResult:
    """Read OPM Flow / Eclipse output files and produce UnifiedResult.

    Args:
        case_path: Path to case base name (without extension), e.g. '/results/SPE1'.
            Will look for .SMSPEC, .UNRST, .EGRID automatically.
        request: Original SimRequest (optional, for metadata).
        unit_system: Override unit system ("FIELD" or "METRIC").
            Auto-detected from SMSPEC if not provided.

    Returns:
        UnifiedResult with cell and well data.
    """
    base = Path(case_path)
    # Handle if extension is included
    if base.suffix in (".SMSPEC", ".UNRST", ".EGRID", ".DATA"):
        base = base.with_suffix("")

    # Find output files
    smspec = _find_file(base, [".SMSPEC"])
    unrst = _find_file(base, [".UNRST"])

    if not smspec and not unrst:
        return _error_result(
            f"No Eclipse output found at {base}", request
        )

    # Read summary (well data + timing)
    summary = None
    if smspec:
        try:
            summary = read_summary(str(smspec))
            if unit_system is None:
                unit_system = summary.get("unit_system", "FIELD")
        except Exception as e:
            logger.error(f"Failed to read summary: {e}")

    if unit_system is None:
        unit_system = "FIELD"

    is_field = unit_system == "FIELD"

    # Read restart (cell data)
    restart_steps = []
    if unrst:
        try:
            restart_steps = read_restart(str(unrst))
        except Exception as e:
            logger.error(f"Failed to read restart: {e}")

    # Build timestep results
    timesteps = _build_timesteps(summary, restart_steps, is_field, request)

    if not timesteps:
        return _error_result("No timesteps extracted from output", request)

    # Grid cells from restart data or request
    n_cells = 0
    if restart_steps and "PRESSURE" in restart_steps[0]:
        n_cells = len(restart_steps[0]["PRESSURE"])
    elif request:
        n_cells = request.grid.total_cells

    return UnifiedResult(
        job_id=f"opm-{base.name}",
        title=request.title if request else base.name,
        status=SimStatus.COMPLETED,
        request=request or _minimal_request(n_cells),
        timesteps=timesteps,
        metadata=SimMetadata(
            backend="opm",
            backend_version="resdata-reader",
            grid_cells=n_cells,
            wall_time_seconds=0,
            converged=True,
            raw_output_path=str(base.parent),
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Internal Functions
# ═══════════════════════════════════════════════════════════════════════════


def _build_timesteps(
    summary: Optional[dict],
    restart_steps: list[dict],
    is_field: bool,
    request: Optional[SimRequest],
) -> list[TimestepResult]:
    """Build TimestepResult list from summary + restart data."""
    conv_p = _psi_to_bar if is_field else (lambda x: x)
    conv_oil = _stbd_to_m3d if is_field else (lambda x: x)
    conv_gas = _mscfd_to_m3d if is_field else (lambda x: x)
    conv_water = _stbd_to_m3d if is_field else (lambda x: x)

    timesteps = []

    if summary:
        days = summary["days"]
        vectors = summary["vectors"]
        wells = summary.get("wells", [])

        for step_idx in range(len(days)):
            time_days = days[step_idx]

            # Cell data from restart (if matching step exists)
            cells = CellData()
            if step_idx < len(restart_steps):
                rst = restart_steps[step_idx]
                if "PRESSURE" in rst:
                    p = rst["PRESSURE"].astype(float)
                    cells.pressure = [conv_p(v) for v in p]
                if "SWAT" in rst:
                    cells.saturation_water = rst["SWAT"].astype(float).tolist()
                if "SGAS" in rst:
                    cells.saturation_gas = rst["SGAS"].astype(float).tolist()
                if cells.saturation_water:
                    sg = cells.saturation_gas or [0.0] * len(cells.saturation_water)
                    cells.saturation_oil = [
                        max(0.0, 1.0 - sw - sgas)
                        for sw, sgas in zip(cells.saturation_water, sg)
                    ]

            # Well data from summary
            well_data = []
            for wname in wells:
                wd = WellData(well_name=wname)

                # BHP
                bhp_key = f"WBHP:{wname}"
                if bhp_key in vectors:
                    wd.bhp_bar = conv_p(float(vectors[bhp_key][step_idx]))

                # Oil rate
                opr_key = f"WOPR:{wname}"
                if opr_key in vectors:
                    wd.oil_rate_m3_day = conv_oil(float(vectors[opr_key][step_idx]))

                # Water rate (production or injection)
                wpr_key = f"WWPR:{wname}"
                wir_key = f"WWIR:{wname}"
                if wpr_key in vectors:
                    wd.water_rate_m3_day = conv_water(float(vectors[wpr_key][step_idx]))
                elif wir_key in vectors:
                    wd.water_rate_m3_day = conv_water(float(vectors[wir_key][step_idx]))

                # Gas rate
                gpr_key = f"WGPR:{wname}"
                gir_key = f"WGIR:{wname}"
                if gpr_key in vectors:
                    wd.gas_rate_m3_day = conv_gas(float(vectors[gpr_key][step_idx]))
                elif gir_key in vectors:
                    wd.gas_rate_m3_day = conv_gas(float(vectors[gir_key][step_idx]))

                well_data.append(wd)

            timesteps.append(TimestepResult(
                time_days=time_days,
                cells=cells,
                wells=well_data,
            ))

    elif restart_steps:
        # Restart only, no summary — limited data
        for step_idx, rst in enumerate(restart_steps):
            cells = CellData()
            if "PRESSURE" in rst:
                p = rst["PRESSURE"].astype(float)
                cells.pressure = [_psi_to_bar(v) if is_field else v for v in p]
            if "SWAT" in rst:
                cells.saturation_water = rst["SWAT"].astype(float).tolist()

            timesteps.append(TimestepResult(
                time_days=float(step_idx + 1) * 30.0,  # Estimate
                cells=cells,
                wells=[],
            ))

    return timesteps


def _find_file(base: Path, extensions: list[str]) -> Optional[Path]:
    """Find Eclipse output file by trying extensions."""
    for ext in extensions:
        path = base.with_suffix(ext)
        if path.exists():
            return path
    return None


def _error_result(msg: str, request: Optional[SimRequest]) -> UnifiedResult:
    """Create error UnifiedResult."""
    return UnifiedResult(
        job_id="opm-error",
        title="Error",
        status=SimStatus.FAILED,
        request=request or _minimal_request(0),
        timesteps=[],
        metadata=SimMetadata(
            backend="opm",
            backend_version="resdata-reader",
            grid_cells=0,
            wall_time_seconds=0,
            converged=False,
            warnings=[msg],
        ),
    )


def _minimal_request(n_cells: int) -> SimRequest:
    """Create minimal SimRequest for cases where no request is available."""
    from clarissa.sim_engine.models import GridParams, WellConfig, WellType, Phase
    # Guess grid from cell count
    n = max(1, int(round(n_cells ** (1/3))))
    return SimRequest(
        grid=GridParams(nx=n, ny=n, nz=max(1, n_cells // (n * n) if n > 0 else 1)),
        wells=[
            WellConfig(name="UNKNOWN", well_type=WellType.PRODUCER,
                       i=0, j=0, bhp_bar=100, phases=[Phase.OIL]),
        ],
        timesteps_days=[],
    )
