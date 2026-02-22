"""OPM Flow Backend — SimulatorBackend implementation for OPM Flow.

Runs the OPM Flow reservoir simulator (via `flow` binary or subprocess)
and parses output using opm.io Python bindings.

Pipeline:
1. Generate Eclipse .DATA deck (via deck_generator)
2. Run `flow CASE.DATA` subprocess
3. Parse .UNRST (restart), .SMSPEC (summary), .EGRID (grid) via opm.io
4. Return UnifiedResult

Issue #163 | Epic #161 | ADR-038
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Optional

from clarissa.sim_engine.backends.base import SimulatorBackend
from clarissa.sim_engine.models import (
    CellData,
    FluidProperties,
    GridParams,
    SimMetadata,
    SimRequest,
    SimStatus,
    TimestepResult,
    UnifiedResult,
    WellConfig,
    WellData,
    WellType,
)

logger = logging.getLogger(__name__)


class OPMBackend(SimulatorBackend):
    """OPM Flow simulator backend.

    Runs OPM Flow via subprocess, reads output via opm.io Python bindings.
    Supports both direct binary execution and Docker-based execution.

    Args:
        flow_binary: Path to `flow` executable (default: search PATH).
        timeout_seconds: Maximum simulation runtime (default: 600).
        use_docker: Run via Docker instead of local binary.
        docker_image: Docker image name when use_docker=True.
    """

    adapter_type: str = "simulator"

    def __init__(
        self,
        flow_binary: str = "flow",
        timeout_seconds: int = 600,
        use_docker: bool = False,
        docker_image: str = "opm-flow:latest",
    ) -> None:
        self._flow_binary = flow_binary
        self._timeout = timeout_seconds
        self._use_docker = use_docker
        self._docker_image = docker_image
        self._flow_available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "opm"

    @property
    def version(self) -> str:
        """Detect OPM Flow version."""
        try:
            result = subprocess.run(
                [self._flow_binary, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            # Parse version from output (usually first line)
            for line in result.stdout.splitlines():
                if "flow" in line.lower() or "opm" in line.lower():
                    return line.strip()
            return result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "not-installed"

    def health_check(self) -> bool:
        """Check if OPM Flow is available."""
        if self._flow_available is not None:
            return self._flow_available

        try:
            if self._use_docker:
                result = subprocess.run(
                    ["docker", "run", "--rm", self._docker_image, "flow", "--version"],
                    capture_output=True, timeout=30,
                )
                self._flow_available = result.returncode == 0
            else:
                result = subprocess.run(
                    [self._flow_binary, "--version"],
                    capture_output=True, timeout=10,
                )
                self._flow_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            self._flow_available = False

        return self._flow_available

    def validate(self, request: SimRequest) -> list[str]:
        """Validate simulation parameters for OPM Flow.

        Checks:
        - Grid size limits (Cloud Run: ~50k cells max)
        - Well placement within grid bounds
        - At least one well
        - Timestep validity
        """
        errors = []
        grid = request.grid

        # Grid size check
        if grid.total_cells > 100_000:
            errors.append(
                f"Grid too large: {grid.total_cells} cells (max 100,000 for OPM backend)"
            )

        # Well bounds check
        for w in request.wells:
            if w.i >= grid.nx:
                errors.append(f"Well '{w.name}': i={w.i} >= nx={grid.nx}")
            if w.j >= grid.ny:
                errors.append(f"Well '{w.name}': j={w.j} >= ny={grid.ny}")
            if w.k_bottom >= grid.nz:
                errors.append(f"Well '{w.name}': k_bottom={w.k_bottom} >= nz={grid.nz}")

        # Timesteps check
        if not request.timesteps_days:
            errors.append("No timesteps defined")
        elif any(t <= 0 for t in request.timesteps_days):
            errors.append("All timesteps must be positive")

        return errors

    def run(
        self,
        request: SimRequest,
        work_dir: str,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> dict[str, Any]:
        """Run OPM Flow simulation.

        Args:
            request: Validated simulation request.
            work_dir: Directory for input/output files.
            on_progress: Progress callback (0-100).

        Returns:
            Raw result dict with paths to output files.

        Raises:
            RuntimeError: If flow binary not found or simulation fails.
        """
        from .registry import register_backend  # Avoid circular at import time
        from clarissa.sim_engine.deck_generator import generate_deck, write_deck

        work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)

        if on_progress:
            on_progress(0)

        # Step 1: Generate deck
        case_name = "CLARISSA_SIM"
        deck_path = str(work_path / f"{case_name}.DATA")
        write_deck(request, deck_path)
        logger.info(f"Deck written to {deck_path}")

        if on_progress:
            on_progress(10)

        # Step 2: Run flow
        t_start = time.time()

        if self._use_docker:
            cmd = self._docker_command(work_path, case_name)
        else:
            cmd = [
                self._flow_binary,
                deck_path,
                f"--output-dir={work_dir}",
            ]

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=work_dir,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"OPM Flow timeout after {self._timeout}s"
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"OPM Flow binary not found: {self._flow_binary}. "
                "Install via: apt install libopm-simulators-bin"
            )

        wall_time = time.time() - t_start

        if on_progress:
            on_progress(80)

        # Step 3: Check for output files
        output_files = {}
        for ext in [".UNRST", ".EGRID", ".SMSPEC", ".UNSMRY", ".INIT", ".PRT"]:
            path = work_path / f"{case_name}{ext}"
            if path.exists():
                output_files[ext.lstrip(".")] = str(path)

        # Check for errors
        errors = []
        if result.returncode != 0:
            errors.append(f"flow exit code: {result.returncode}")
            if result.stderr:
                errors.extend(
                    line.strip()
                    for line in result.stderr.splitlines()[:10]
                    if line.strip()
                )

        # Parse PRT for warnings
        prt_path = work_path / f"{case_name}.PRT"
        warnings = []
        if prt_path.exists():
            prt_text = prt_path.read_text(errors="replace")
            if "Error" in prt_text or "ERROR" in prt_text:
                for line in prt_text.splitlines():
                    if "error" in line.lower() and len(line.strip()) < 200:
                        errors.append(line.strip())

        if on_progress:
            on_progress(90)

        converged = result.returncode == 0 and "UNRST" in output_files

        return {
            "case_name": case_name,
            "work_dir": work_dir,
            "output_files": output_files,
            "wall_time_seconds": wall_time,
            "exit_code": result.returncode,
            "converged": converged,
            "errors": errors[:10],
            "warnings": warnings[:10],
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
        }

    def parse_result(
        self,
        raw: dict[str, Any],
        request: SimRequest,
    ) -> UnifiedResult:
        """Parse OPM Flow output into UnifiedResult.

        Uses opm.io to read:
        - .UNRST: Per-cell PRESSURE, SWAT, SGAS at each report step
        - .SMSPEC/.UNSMRY: Per-well summary data (rates, BHP, cumulative)
        - .EGRID: Grid verification

        Args:
            raw: Output from run() with file paths.
            request: Original request for context.

        Returns:
            UnifiedResult with timestep data.
        """
        job_id = raw.get("job_id", "opm-unknown")
        output_files = raw.get("output_files", {})
        work_dir = raw.get("work_dir", "")
        case_name = raw.get("case_name", "CLARISSA_SIM")

        # If simulation didn't converge, return error result
        if not raw.get("converged", False):
            return UnifiedResult(
                job_id=job_id,
                title=request.title,
                status=SimStatus.FAILED,
                request=request,
                timesteps=[],
                metadata=SimMetadata(
                    backend="opm",
                    backend_version=self.version,
                    grid_cells=request.grid.total_cells,
                    wall_time_seconds=raw.get("wall_time_seconds", 0),
                    converged=False,
                    warnings=raw.get("errors", []),
                ),
            )

        # Parse output files
        timesteps = []
        summary_data = {}

        # Read restart file (.UNRST)
        if "UNRST" in output_files:
            timesteps = self._parse_restart(
                output_files["UNRST"],
                request,
            )

        # Read summary data (.SMSPEC)
        if "SMSPEC" in output_files:
            summary_data = self._parse_summary(
                output_files["SMSPEC"],
                request,
            )

        # Merge summary well data into timestep results
        if summary_data and timesteps:
            timesteps = self._merge_well_data(timesteps, summary_data, request)

        return UnifiedResult(
            job_id=job_id,
            title=request.title,
            status=SimStatus.COMPLETED,
            request=request,
            timesteps=timesteps,
            metadata=SimMetadata(
                backend="opm",
                backend_version=self.version,
                grid_cells=request.grid.total_cells,
                wall_time_seconds=raw.get("wall_time_seconds", 0),
                solver_iterations=0,  # TODO: parse from PRT
                converged=True,
                raw_output_path=work_dir,
            ),
        )

    # ─── Internal Parsers ─────────────────────────────────────────────

    def _parse_restart(
        self,
        unrst_path: str,
        request: SimRequest,
    ) -> list[TimestepResult]:
        """Parse .UNRST restart file for per-cell data."""
        try:
            from opm.io.ecl import ERst
        except ImportError:
            logger.warning("opm.io.ecl not available — skipping restart parse")
            return []

        try:
            rst = ERst(unrst_path)
        except Exception as e:
            logger.error(f"Failed to open UNRST: {e}")
            return []

        steps = rst.report_steps
        n_cells = request.grid.total_cells
        requested_days = set(request.timesteps_days)

        timesteps = []

        for step_idx in steps:
            try:
                # Get arrays at this step
                arrays = {name: arr_type for name, arr_type, size in rst.arrays(step_idx)}

                # Read pressure (always present)
                pressure = list(rst["PRESSURE", step_idx]) if "PRESSURE" in arrays else []

                # Read saturations
                swat = list(rst["SWAT", step_idx]) if "SWAT" in arrays else []
                sgas = list(rst["SGAS", step_idx]) if "SGAS" in arrays else []

                # Oil saturation = 1 - Sw - Sg
                so = []
                if swat:
                    so = [
                        1.0 - swat[i] - (sgas[i] if sgas else 0.0)
                        for i in range(len(swat))
                    ]

                # Approximate time from step index
                # (precise time comes from summary data, merged later)
                time_days = self._step_to_days(step_idx, steps, request.timesteps_days)

                timesteps.append(TimestepResult(
                    time_days=time_days,
                    cells=CellData(
                        pressure=pressure,
                        saturation_water=swat,
                        saturation_oil=so,
                        saturation_gas=sgas,
                    ),
                    wells=[],  # Filled from summary data
                ))

            except Exception as e:
                logger.warning(f"Failed to parse restart step {step_idx}: {e}")
                continue

        return timesteps

    def _parse_summary(
        self,
        smspec_path: str,
        request: SimRequest,
    ) -> dict[str, Any]:
        """Parse .SMSPEC/.UNSMRY summary file for well and field data."""
        try:
            from opm.io.ecl import ESmry
        except ImportError:
            logger.warning("opm.io.ecl not available — skipping summary parse")
            return {}

        try:
            smry = ESmry(smspec_path)
        except Exception as e:
            logger.error(f"Failed to open SMSPEC: {e}")
            return {}

        keys = list(smry.keys())
        result = {"keys": keys}

        # Time vector
        if "TIME" in keys:
            result["TIME"] = list(smry["TIME"])

        # Field data
        for key in ["FOPR", "FWPR", "FGOR", "FOPT", "FWPT"]:
            if key in keys:
                result[key] = list(smry[key])

        # Per-well data
        for well in request.wells:
            wname = well.name
            for prefix in ["WOPR", "WWPR", "WGPR", "WBHP", "WWIR", "WGIR",
                           "WOPT", "WWPT", "WOIT", "WWIT"]:
                key = f"{prefix}:{wname}"
                if key in keys:
                    result[key] = list(smry[key])

        return result

    def _merge_well_data(
        self,
        timesteps: list[TimestepResult],
        summary: dict[str, Any],
        request: SimRequest,
    ) -> list[TimestepResult]:
        """Merge summary well data into restart timestep results."""
        time_vec = summary.get("TIME", [])
        if not time_vec:
            return timesteps

        import numpy as np

        time_arr = np.array(time_vec)

        for ts in timesteps:
            # Find closest summary time index
            idx = int(np.argmin(np.abs(time_arr - ts.time_days)))

            well_data = []
            for well in request.wells:
                wname = well.name
                wd = WellData(
                    well_name=wname,
                    oil_rate_m3_day=self._safe_get(summary, f"WOPR:{wname}", idx, 0.0),
                    water_rate_m3_day=(
                        self._safe_get(summary, f"WWIR:{wname}", idx, 0.0)
                        if well.well_type == WellType.INJECTOR
                        else self._safe_get(summary, f"WWPR:{wname}", idx, 0.0)
                    ),
                    gas_rate_m3_day=self._safe_get(summary, f"WGPR:{wname}", idx, 0.0),
                    bhp_bar=self._safe_get(summary, f"WBHP:{wname}", idx, 0.0) / 14.5038,
                    cumulative_oil_m3=self._safe_get(summary, f"WOPT:{wname}", idx, 0.0),
                    cumulative_water_m3=(
                        self._safe_get(summary, f"WWIT:{wname}", idx, 0.0)
                        if well.well_type == WellType.INJECTOR
                        else self._safe_get(summary, f"WWPT:{wname}", idx, 0.0)
                    ),
                )
                well_data.append(wd)

            ts.wells = well_data

        return timesteps

    # ─── Helpers ──────────────────────────────────────────────────────

    def _docker_command(self, work_path: Path, case_name: str) -> list[str]:
        """Build Docker run command."""
        return [
            "docker", "run", "--rm",
            "-v", f"{work_path.resolve()}:/simulation",
            "-w", "/simulation",
            self._docker_image,
            "flow", f"{case_name}.DATA",
            "--output-dir=/simulation",
        ]

    @staticmethod
    def _step_to_days(
        step_idx: int,
        all_steps: list[int],
        requested_days: list[float],
    ) -> float:
        """Approximate simulation day from step index.

        Uses linear interpolation between step 0 and max requested day.
        Accurate time comes from summary data merge.
        """
        if not all_steps or not requested_days:
            return float(step_idx)
        max_day = max(requested_days)
        max_step = max(all_steps)
        if max_step == 0:
            return 0.0
        return (step_idx / max_step) * max_day

    @staticmethod
    def _safe_get(data: dict, key: str, idx: int, default: float = 0.0) -> float:
        """Safely get a value from summary data."""
        arr = data.get(key, [])
        if arr and 0 <= idx < len(arr):
            return float(arr[idx])
        return default


# ─── Auto-register on import ─────────────────────────────────────────────

def _auto_register() -> None:
    """Register OPM backend in the global registry if available."""
    try:
        from clarissa.sim_engine.backends.registry import register_backend
        backend = OPMBackend()
        register_backend(backend)
        logger.info("OPM backend registered")
    except Exception as e:
        logger.debug(f"OPM backend auto-registration skipped: {e}")
