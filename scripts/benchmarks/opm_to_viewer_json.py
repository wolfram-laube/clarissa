#!/usr/bin/env python3
"""CLARISSA · OPM Flow Results → Viewer JSON Converter.

Reads OPM Flow simulation output (UNRST, SMSPEC, EGRID, INIT) using resdata
and produces JSON compatible with spe-viewer.html.

For large grids (SPE10 M2: 1.1M cells), applies spatial subsampling to keep
the JSON size manageable for browser rendering.

Usage:
    python3 opm_to_viewer_json.py --results-dir ~/projects/results/clarissa-benchmarks \\
                                   --output spe_benchmarks.json \\
                                   --benchmarks spe1 spe5 spe9 spe10m1 spe10m2

Requirements:
    pip install resdata numpy (available in ~/venv on Nordic VM)

Issue: CLARISSA Sim-Engine · ADR-040
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from resdata.grid import Grid
    from resdata.resfile import ResdataFile
    from resdata.summary import Summary
except ImportError:
    print("ERROR: resdata not installed. Run: pip install resdata")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("opm2json")


# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BenchmarkConfig:
    """Configuration for each benchmark."""
    key: str
    name: str
    description: str
    deck_basename: str  # e.g. "SPE1CASE2" (without .DATA)
    nx: int
    ny: int
    nz: int
    max_timesteps: int = 25
    subsample: Optional[tuple[int, int, int]] = None  # (step_x, step_y, step_z)
    max_wells: int = 30


BENCHMARKS = {
    "spe1": BenchmarkConfig(
        key="SPE1", name="SPE1 — Gas Injection",
        description="Three-phase black-oil, gas injection (Odeh, 1981)",
        deck_basename="SPE1CASE2", nx=10, ny=10, nz=3,
    ),
    "spe5": BenchmarkConfig(
        key="SPE5", name="SPE5 — WAG Miscible",
        description="Miscible flood with solvent, WAG cycles (Killough, 1987)",
        deck_basename="SPE5CASE1", nx=7, ny=7, nz=3,
    ),
    "spe9": BenchmarkConfig(
        key="SPE9", name="SPE9 — 26 Wells",
        description="Corner-point, heterogeneous, 26 wells (Killough, 1995)",
        deck_basename="SPE9_CP", nx=24, ny=25, nz=15,
        max_timesteps=15,
    ),
    "spe10m1": BenchmarkConfig(
        key="SPE10", name="SPE10 M1 — Upscaling",
        description="2D cross-section, upscaling benchmark (Christie & Blunt, 2001)",
        deck_basename="SPE10_MODEL1", nx=100, ny=1, nz=20,
    ),
    "spe10m2": BenchmarkConfig(
        key="SPE10M2", name="SPE10 M2 — Full 3D",
        description="1.1M-cell heterogeneous model, subsampled (Christie & Blunt, 2001)",
        deck_basename="SPE10_MODEL2", nx=60, ny=220, nz=85,
        max_timesteps=12,
        subsample=(3, 11, 4),  # 60/3=20, 220/11=20, 85/4≈21 → ~8400 cells
        max_wells=5,
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# File Discovery
# ═══════════════════════════════════════════════════════════════════════

def find_opm_files(result_dir: Path, basename: str) -> dict[str, Path]:
    """Find OPM output files in result directory."""
    files = {}
    extensions = {
        "UNRST": [".UNRST"],
        "SMSPEC": [".SMSPEC"],
        "UNSMRY": [".UNSMRY"],
        "EGRID": [".EGRID"],
        "INIT": [".INIT"],
    }

    for key, exts in extensions.items():
        for ext in exts:
            candidate = result_dir / f"{basename}{ext}"
            if candidate.exists():
                files[key] = candidate
                break

    return files


# ═══════════════════════════════════════════════════════════════════════
# Grid Data Extraction
# ═══════════════════════════════════════════════════════════════════════

def extract_static_properties(
    init_file: ResdataFile,
    grid: Grid,
    config: BenchmarkConfig,
) -> dict:
    """Extract static grid properties (PERMX, PORO) from .INIT file."""
    nx, ny, nz = config.nx, config.ny, config.nz
    ncells = nx * ny * nz
    sub = config.subsample

    def extract_array(keyword: str, default: float = 0.0) -> list[float]:
        """Extract and optionally subsample a property array."""
        if init_file.has_kw(keyword):
            kw = init_file[keyword][0]
            raw = np.array([kw[i] for i in range(min(len(kw), ncells))])
        else:
            raw = np.full(ncells, default)

        if sub is None:
            return raw.tolist()

        # Subsample: reshape to 3D, pick every Nth
        arr3d = raw.reshape(nz, ny, nx)
        sampled = arr3d[::sub[2], ::sub[1], ::sub[0]]
        return sampled.flatten().tolist()

    return {
        "permx": extract_array("PERMX", 100.0),
        "poro": extract_array("PORO", 0.2),
    }


def extract_restart_timestep(
    rst_file: ResdataFile,
    report_step: int,
    config: BenchmarkConfig,
) -> dict:
    """Extract cell data for one restart report step."""
    nx, ny, nz = config.nx, config.ny, config.nz
    ncells = nx * ny * nz
    sub = config.subsample

    def get_field(keyword: str, step_index: int, default: float = 0.0) -> list[float]:
        if not rst_file.has_kw(keyword):
            return []

        kws = rst_file[keyword]
        if step_index >= len(kws):
            return []

        kw = kws[step_index]
        raw = np.array([kw[i] for i in range(min(len(kw), ncells))])

        if sub is None:
            return [round(float(v), 4) for v in raw]

        arr3d = raw.reshape(nz, ny, nx)
        sampled = arr3d[::sub[2], ::sub[1], ::sub[0]]
        return [round(float(v), 4) for v in sampled.flatten()]

    # Find the index for this report step in the restart file
    report_steps = rst_file.report_steps
    try:
        idx = report_steps.index(report_step)
    except (ValueError, AttributeError):
        # Fallback: use position directly
        idx = report_step

    cells = {
        "pressure": get_field("PRESSURE", idx),
        "saturation_oil": get_field("SOIL", idx),
        "saturation_water": get_field("SWAT", idx),
        "saturation_gas": get_field("SGAS", idx),
    }

    # Convert pressure from psi to bar if FIELD units
    if cells["pressure"]:
        cells["pressure"] = [round(p * 0.0689476, 2) for p in cells["pressure"]]

    return cells


# ═══════════════════════════════════════════════════════════════════════
# Summary (Well) Data Extraction
# ═══════════════════════════════════════════════════════════════════════

def extract_well_data(
    summary: Summary,
    time_days: float,
    config: BenchmarkConfig,
) -> list[dict]:
    """Extract well data at a given time from summary file."""
    wells = []

    # Get well list from summary keys
    well_names = set()
    for key in summary.keys():
        parts = str(key).split(":")
        if len(parts) >= 2 and parts[0] in ("WOPR", "WWPR", "WGPR", "WBHP"):
            well_names.add(parts[1])

    for wname in sorted(well_names)[:config.max_wells]:
        well = {"well_name": wname}

        for smry_key, json_key, conv in [
            (f"WOPR:{wname}", "oil_rate_m3_day", 0.158987),    # STB/d → m³/d
            (f"WWPR:{wname}", "water_rate_m3_day", 0.158987),
            (f"WGPR:{wname}", "gas_rate_m3_day", 28.3168),      # Mscf/d → m³/d
            (f"WBHP:{wname}", "bhp_bar", 0.0689476),            # psi → bar
            (f"WOPT:{wname}", "cumulative_oil_m3", 0.158987),
            (f"WWPT:{wname}", "cumulative_water_m3", 0.158987),
            (f"WWIR:{wname}", "water_rate_m3_day", 0.158987),   # injector water
            (f"WGIR:{wname}", "gas_rate_m3_day", 28.3168),      # injector gas
        ]:
            try:
                if summary.has_key(smry_key):
                    val = float(summary.numpy_vector(smry_key, time_index=None)[-1])
                    # Find closest time
                    times = summary.numpy_vector("TIME")
                    closest_idx = int(np.argmin(np.abs(times - time_days)))
                    val = float(summary.numpy_vector(smry_key)[closest_idx])
                    well[json_key] = round(val * conv, 2)
            except Exception:
                pass

        # Fill defaults
        for k in ["oil_rate_m3_day", "water_rate_m3_day", "gas_rate_m3_day",
                   "bhp_bar", "cumulative_oil_m3", "cumulative_water_m3"]:
            well.setdefault(k, 0.0)

        wells.append(well)

    return wells


# ═══════════════════════════════════════════════════════════════════════
# Main Converter
# ═══════════════════════════════════════════════════════════════════════

def convert_benchmark(result_dir: Path, config: BenchmarkConfig) -> Optional[dict]:
    """Convert one benchmark's OPM output to viewer JSON."""
    log.info(f"Converting {config.key} from {result_dir}")

    files = find_opm_files(result_dir, config.deck_basename)
    required = {"UNRST", "SMSPEC", "UNSMRY"}
    missing = required - set(files.keys())
    if missing:
        log.error(f"  Missing files: {missing}")
        log.error(f"  Found: {list(files.keys())}")
        return None

    # Load files
    log.info(f"  Loading restart file: {files['UNRST']}")
    rst = ResdataFile(str(files["UNRST"]))

    log.info(f"  Loading summary: {files['SMSPEC']}")
    smry = Summary(str(files["SMSPEC"]))

    init = None
    if "INIT" in files:
        log.info(f"  Loading INIT: {files['INIT']}")
        init = ResdataFile(str(files["INIT"]))

    grid_obj = None
    if "EGRID" in files:
        log.info(f"  Loading grid: {files['EGRID']}")
        grid_obj = Grid(str(files["EGRID"]))

    # Get report step times
    times = smry.numpy_vector("TIME")  # days
    report_steps = list(range(1, len(rst.report_steps) + 1)) if hasattr(rst, 'report_steps') else list(range(1, int(times[-1]) + 1))

    # Select timesteps (subsample if too many)
    n_available = len(times)
    step = max(1, n_available // config.max_timesteps)
    selected_indices = list(range(0, n_available, step))
    if selected_indices[-1] != n_available - 1:
        selected_indices.append(n_available - 1)

    log.info(f"  Report steps: {n_available} available, {len(selected_indices)} selected")

    # Subsampled grid dimensions
    sub = config.subsample
    if sub:
        snx = len(range(0, config.nx, sub[0]))
        sny = len(range(0, config.ny, sub[1]))
        snz = len(range(0, config.nz, sub[2]))
        log.info(f"  Subsampling: {config.nx}×{config.ny}×{config.nz} → {snx}×{sny}×{snz} ({snx*sny*snz} cells)")
    else:
        snx, sny, snz = config.nx, config.ny, config.nz

    # Extract static properties
    static_props = {"permx": [100.0] * (snx*sny*snz), "poro": [0.2] * (snx*sny*snz)}
    if init:
        static_props = extract_static_properties(init, grid_obj, config)
        log.info(f"  Static: permx[{len(static_props['permx'])}], poro[{len(static_props['poro'])}]")

    # Extract timesteps
    timesteps = []
    wall_time_file = result_dir / "wall_time.txt"
    wall_time = float(wall_time_file.read_text().strip()) if wall_time_file.exists() else 0.0

    for ti in selected_indices:
        t_days = float(times[ti])
        log.info(f"  Step {ti}/{n_available}: day {t_days:.0f}")

        # Cell data from restart
        cells = extract_restart_timestep(rst, ti, config)

        # Well data from summary
        wells = extract_well_data(smry, t_days, config)

        timesteps.append({
            "time_days": round(t_days, 1),
            "cells": cells,
            "wells": wells,
        })

    # Well positions from grid
    well_positions = {}
    if grid_obj:
        # Try to get well positions from COMPDAT in summary
        for wname in set(w["well_name"] for ts in timesteps for w in ts.get("wells", [])):
            well_positions[wname] = {"i": 0, "j": 0, "k": 0}  # Fallback

    # Build result
    total_days = float(times[-1]) if len(times) > 0 else 0

    result = {
        "opm": {
            "job_id": f"{config.key.lower()}-opm-flow-001",
            "title": f"{config.key} — OPM Flow",
            "status": "completed",
            "timesteps": timesteps,
            "metadata": {
                "backend": "OPM Flow",
                "backend_version": "2025.10",
                "grid_cells": snx * sny * snz,
                "wall_time_seconds": wall_time,
                "solver_iterations": 0,
                "converged": True,
                "warnings": [],
            },
        },
        # MRST placeholder — fill in when MRST results available
        "mrst": {
            "job_id": f"{config.key.lower()}-mrst-pending",
            "title": f"{config.key} — MRST (pending)",
            "status": "pending",
            "timesteps": timesteps,  # Use OPM data as placeholder
            "metadata": {
                "backend": "MRST (placeholder)",
                "backend_version": "pending",
                "grid_cells": snx * sny * snz,
                "wall_time_seconds": 0,
                "solver_iterations": 0,
                "converged": True,
                "warnings": ["MRST results not yet available — showing OPM data as placeholder"],
            },
        },
        "grid": {
            "nx": snx,
            "ny": sny,
            "nz": snz,
            "original_nx": config.nx,
            "original_ny": config.ny,
            "original_nz": config.nz,
            "subsampled": sub is not None,
            "subsample_factor": list(sub) if sub else None,
            **static_props,
            "well_positions": well_positions,
        },
        "deck_info": {
            "file": f"{config.deck_basename}.DATA",
            "phases": [],  # Would need deck parsing
            "units": "FIELD",
            "wells": len(well_positions),
            "total_days": total_days,
            "description": config.description,
        },
    }

    log.info(f"  ✓ {config.key}: {len(timesteps)} timesteps, {snx}×{sny}×{snz} grid")
    return result


def main():
    parser = argparse.ArgumentParser(description="Convert OPM Flow results to viewer JSON")
    parser.add_argument("--results-dir", required=True, help="Base results directory")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--benchmarks", nargs="+", required=True, help="Benchmark keys to convert")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    benchmarks_data = {}
    index = []

    for bm_key in args.benchmarks:
        if bm_key not in BENCHMARKS:
            log.warning(f"Unknown benchmark: {bm_key}")
            continue

        config = BENCHMARKS[bm_key]
        bm_dir = results_dir / bm_key

        if not bm_dir.exists():
            log.warning(f"Results dir not found: {bm_dir}")
            continue

        result = convert_benchmark(bm_dir, config)
        if result:
            benchmarks_data[config.key] = result

            sub = config.subsample
            grid_str = f"{result['grid']['nx']}×{result['grid']['ny']}×{result['grid']['nz']}"
            if sub:
                grid_str += f" (from {config.nx}×{config.ny}×{config.nz})"

            index.append({
                "id": config.key,
                "name": config.name,
                "grid": grid_str,
                "cells": result["grid"]["nx"] * result["grid"]["ny"] * result["grid"]["nz"],
                "wells": len(result["grid"]["well_positions"]),
                "years": f"{result['deck_info']['total_days']/365.25:.1f}y",
                "description": config.description,
            })

    if not benchmarks_data:
        log.error("No benchmarks converted!")
        sys.exit(1)

    combined = {
        "benchmarks": benchmarks_data,
        "index": index,
    }

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(combined, f, separators=(",", ":"))

    size_mb = output_path.stat().st_size / 1e6
    log.info(f"\n{'='*60}")
    log.info(f"Output: {output_path} ({size_mb:.1f} MB)")
    log.info(f"Benchmarks: {list(benchmarks_data.keys())}")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
