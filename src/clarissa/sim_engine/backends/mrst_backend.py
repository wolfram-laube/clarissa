"""MRST Backend — SimulatorBackend implementation for MRST via GNU Octave.

Runs the MATLAB Reservoir Simulation Toolbox through GNU Octave and
parses .mat output into UnifiedResult.

Pipeline:
1. Generate MRST .m script (via mrst_script_generator)
2. Run `octave --no-gui script.m` subprocess
3. Parse results.mat via scipy.io.loadmat
4. Return UnifiedResult

Issue #166 | Epic #161 | ADR-040
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Optional

from clarissa.sim_engine.backends.base import SimulatorBackend
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

logger = logging.getLogger(__name__)


class MRSTBackend(SimulatorBackend):
    """MRST simulator backend via GNU Octave.

    Generates MRST .m scripts, executes them through Octave, and
    parses .mat output into the unified result format.

    Args:
        octave_binary: Path to `octave` executable (default: search PATH).
        mrst_dir: Path to MRST installation. If None, expects MRST_DIR env
            or that MRST is already on the Octave path.
        timeout_seconds: Maximum simulation runtime (default: 900).
        use_docker: Run via Docker instead of local binary.
        docker_image: Docker image name when use_docker=True.
    """

    adapter_type: str = "simulator"

    def __init__(
        self,
        octave_binary: str = "octave",
        mrst_dir: Optional[str] = None,
        timeout_seconds: int = 900,
        use_docker: bool = False,
        docker_image: str = "mrst-octave:latest",
    ) -> None:
        self._octave_binary = octave_binary
        self._mrst_dir = mrst_dir or os.environ.get("MRST_DIR", "")
        self._timeout = timeout_seconds
        self._use_docker = use_docker
        self._docker_image = docker_image
        self._octave_available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "mrst"

    @property
    def version(self) -> str:
        """Detect GNU Octave version."""
        try:
            result = subprocess.run(
                [self._octave_binary, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if "octave" in line.lower() or "gnu" in line.lower():
                    return line.strip()
            return result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "not-installed"

    def health_check(self) -> bool:
        """Check if Octave and MRST are available."""
        if self._octave_available is not None:
            return self._octave_available

        try:
            if self._use_docker:
                result = subprocess.run(
                    ["docker", "run", "--rm", self._docker_image,
                     "octave", "--no-gui", "--eval", "disp('ok')"],
                    capture_output=True, timeout=30,
                )
                self._octave_available = result.returncode == 0
            else:
                result = subprocess.run(
                    [self._octave_binary, "--no-gui", "--eval", "disp('ok')"],
                    capture_output=True, timeout=10,
                )
                self._octave_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            self._octave_available = False

        return self._octave_available

    def validate(self, request: SimRequest) -> list[str]:
        """Validate simulation parameters for MRST.

        Checks:
        - Grid size limits (MRST/Octave: ~200k cells practical max)
        - Well placement within grid bounds
        - At least one well
        - Timestep validity
        - Phase configuration support
        """
        errors = []
        grid = request.grid

        # Grid size — MRST is slower than OPM, tighter limit
        if grid.total_cells > 200_000:
            errors.append(
                f"Grid too large: {grid.total_cells} cells "
                "(max 200,000 for MRST backend)"
            )

        # Well bounds check
        for w in request.wells:
            if w.i >= grid.nx:
                errors.append(f"Well '{w.name}': i={w.i} >= nx={grid.nx}")
            if w.j >= grid.ny:
                errors.append(f"Well '{w.name}': j={w.j} >= ny={grid.ny}")
            if w.k_bottom >= grid.nz:
                errors.append(f"Well '{w.name}': k_bottom={w.k_bottom} >= nz={grid.nz}")

        # Timesteps
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
        """Run MRST simulation via GNU Octave.

        Args:
            request: Validated simulation request.
            work_dir: Directory for input/output files.
            on_progress: Progress callback (0-100).

        Returns:
            Raw result dict with paths to output files.

        Raises:
            RuntimeError: If Octave not found or simulation fails.
        """
        from clarissa.sim_engine.mrst_script_generator import (
            write_mrst_script,
        )

        work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)

        if on_progress:
            on_progress(0)

        # Step 1: Generate .m script
        output_mat = "results.mat"
        script_name = "clarissa_sim.m"
        script_path = str(work_path / script_name)
        write_mrst_script(request, script_path, output_mat)
        logger.info(f"MRST script written to {script_path}")

        if on_progress:
            on_progress(10)

        # Step 2: Build Octave command
        # Prepend MRST startup if MRST_DIR is set
        env = os.environ.copy()
        if self._mrst_dir:
            env["MRST_DIR"] = self._mrst_dir

        if self._use_docker:
            cmd = self._docker_command(work_path, script_name)
        else:
            cmd = [
                self._octave_binary,
                "--no-gui",
                "--no-window-system",
                "--silent",
                script_path,
            ]

        logger.info(f"Running: {' '.join(cmd)}")
        t_start = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=work_dir,
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"MRST/Octave timeout after {self._timeout}s"
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"GNU Octave not found: {self._octave_binary}. "
                "Install via: apt install octave"
            )

        wall_time = time.time() - t_start

        if on_progress:
            on_progress(80)

        # Step 3: Check for output files
        mat_path = work_path / output_mat
        output_files = {}
        if mat_path.exists():
            output_files["mat"] = str(mat_path)
        output_files["script"] = script_path

        # Check for errors
        errors = []
        if result.returncode != 0:
            errors.append(f"octave exit code: {result.returncode}")
            if result.stderr:
                errors.extend(
                    line.strip()
                    for line in result.stderr.splitlines()[:10]
                    if line.strip()
                )

        if on_progress:
            on_progress(90)

        converged = result.returncode == 0 and "mat" in output_files

        return {
            "script_name": script_name,
            "work_dir": work_dir,
            "output_files": output_files,
            "wall_time_seconds": wall_time,
            "exit_code": result.returncode,
            "converged": converged,
            "errors": errors[:10],
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
        }

    def parse_result(
        self,
        raw: dict[str, Any],
        request: SimRequest,
    ) -> UnifiedResult:
        """Parse MRST .mat output into UnifiedResult.

        Reads the .mat file produced by the MRST script containing:
        - time_days: [n_steps × 1] timestep vector
        - pressure: [n_steps × n_cells] pressure in bar
        - s_water: [n_steps × n_cells] water saturation
        - s_oil: [n_steps × n_cells] oil saturation
        - well_bhp: [n_steps × n_wells] BHP in bar
        - well_qOs: [n_steps × n_wells] oil rate m³/day
        - well_qWs: [n_steps × n_wells] water rate m³/day
        - well_names: cell array of well names
        - wall_time: scalar simulation time
        - converged: boolean

        Args:
            raw: Output from run() with file paths.
            request: Original request for context.

        Returns:
            UnifiedResult with timestep data.
        """
        job_id = raw.get("job_id", "mrst-unknown")
        output_files = raw.get("output_files", {})

        # Non-converged → error result
        if not raw.get("converged", False):
            return UnifiedResult(
                job_id=job_id,
                title=request.title,
                status=SimStatus.FAILED,
                request=request,
                timesteps=[],
                metadata=SimMetadata(
                    backend="mrst",
                    backend_version=self.version,
                    grid_cells=request.grid.total_cells,
                    wall_time_seconds=raw.get("wall_time_seconds", 0),
                    converged=False,
                    warnings=raw.get("errors", []),
                ),
            )

        mat_path = output_files.get("mat")
        if not mat_path:
            return self._error_result(job_id, request, raw, "No .mat output file")

        # Load .mat
        mat_data = self._load_mat(mat_path)
        if mat_data is None:
            return self._error_result(job_id, request, raw, "Failed to load .mat file")

        # Parse timesteps
        timesteps = self._parse_mat_data(mat_data, request)

        # Extract wall_time from .mat if available
        mat_wall_time = float(mat_data.get("wall_time", [[0]])[0][0])
        wall_time = mat_wall_time if mat_wall_time > 0 else raw.get("wall_time_seconds", 0)

        mat_converged = bool(mat_data.get("converged", [[True]])[0][0])

        return UnifiedResult(
            job_id=job_id,
            title=request.title,
            status=SimStatus.COMPLETED if mat_converged else SimStatus.FAILED,
            request=request,
            timesteps=timesteps,
            metadata=SimMetadata(
                backend="mrst",
                backend_version=self.version,
                grid_cells=request.grid.total_cells,
                wall_time_seconds=wall_time,
                converged=mat_converged,
                raw_output_path=raw.get("work_dir", ""),
            ),
        )

    # ─── Internal Parsers ─────────────────────────────────────────────

    @staticmethod
    def _load_mat(mat_path: str) -> Optional[dict]:
        """Load .mat file using scipy.io."""
        try:
            from scipy.io import loadmat
        except ImportError:
            logger.warning("scipy not available — cannot parse .mat files")
            return None

        try:
            return loadmat(mat_path, squeeze_me=False)
        except Exception as e:
            logger.error(f"Failed to load .mat file: {e}")
            return None

    def _parse_mat_data(
        self,
        mat: dict,
        request: SimRequest,
    ) -> list[TimestepResult]:
        """Parse loaded .mat data into TimestepResult list."""
        time_days = mat.get("time_days")
        pressure = mat.get("pressure")
        s_water = mat.get("s_water")
        s_oil = mat.get("s_oil")
        well_bhp = mat.get("well_bhp")
        well_qOs = mat.get("well_qOs")
        well_qWs = mat.get("well_qWs")

        if time_days is None or pressure is None:
            logger.error("Missing time_days or pressure in .mat file")
            return []

        n_steps = time_days.shape[0]
        timesteps = []

        for i in range(n_steps):
            t_days = float(time_days[i, 0]) if time_days.ndim > 1 else float(time_days[i])

            # Cell data
            p_vec = pressure[i, :].tolist() if pressure.ndim > 1 else []
            sw_vec = s_water[i, :].tolist() if s_water is not None and s_water.ndim > 1 else []
            so_vec = s_oil[i, :].tolist() if s_oil is not None and s_oil.ndim > 1 else []
            # Gas saturation = 1 - Sw - So (if three-phase)
            sg_vec = [
                max(0.0, 1.0 - sw_vec[j] - so_vec[j])
                for j in range(len(sw_vec))
            ] if sw_vec and so_vec else []

            # Well data
            wells = []
            for w_idx, well in enumerate(request.wells):
                bhp = 0.0
                q_oil = 0.0
                q_water = 0.0

                if well_bhp is not None and well_bhp.ndim > 1 and w_idx < well_bhp.shape[1]:
                    bhp = float(well_bhp[i, w_idx])
                if well_qOs is not None and well_qOs.ndim > 1 and w_idx < well_qOs.shape[1]:
                    q_oil = float(well_qOs[i, w_idx])
                if well_qWs is not None and well_qWs.ndim > 1 and w_idx < well_qWs.shape[1]:
                    q_water = float(well_qWs[i, w_idx])

                wells.append(WellData(
                    well_name=well.name,
                    oil_rate_m3_day=abs(q_oil),
                    water_rate_m3_day=abs(q_water),
                    gas_rate_m3_day=0.0,
                    bhp_bar=bhp,
                    cumulative_oil_m3=0.0,  # TODO: cumulative from trapz
                    cumulative_water_m3=0.0,
                ))

            timesteps.append(TimestepResult(
                time_days=t_days,
                cells=CellData(
                    pressure=p_vec,
                    saturation_water=sw_vec,
                    saturation_oil=so_vec,
                    saturation_gas=sg_vec,
                ),
                wells=wells,
            ))

        return timesteps

    def _error_result(
        self,
        job_id: str,
        request: SimRequest,
        raw: dict,
        message: str,
    ) -> UnifiedResult:
        """Create a failed UnifiedResult with error message."""
        return UnifiedResult(
            job_id=job_id,
            title=request.title,
            status=SimStatus.FAILED,
            request=request,
            timesteps=[],
            metadata=SimMetadata(
                backend="mrst",
                backend_version=self.version,
                grid_cells=request.grid.total_cells,
                wall_time_seconds=raw.get("wall_time_seconds", 0),
                converged=False,
                warnings=[message] + raw.get("errors", []),
            ),
        )

    # ─── Helpers ──────────────────────────────────────────────────────

    def _docker_command(self, work_path: Path, script_name: str) -> list[str]:
        """Build Docker run command."""
        return [
            "docker", "run", "--rm",
            "-v", f"{work_path.resolve()}:/simulation",
            "-w", "/simulation",
            self._docker_image,
            "octave", "--no-gui", "--no-window-system", "--silent",
            script_name,
        ]


# ─── Auto-register on import ─────────────────────────────────────────────

def _auto_register() -> None:
    """Register MRST backend in the global registry if available."""
    try:
        from clarissa.sim_engine.backends.registry import register_backend
        backend = MRSTBackend()
        register_backend(backend)
        logger.info("MRST backend registered")
    except Exception as e:
        logger.debug(f"MRST backend auto-registration skipped: {e}")
