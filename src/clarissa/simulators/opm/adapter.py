"""OPM Flow simulator adapter.

Integrates the Open Porous Media (OPM) Flow reservoir simulator with CLARISSA.
OPM Flow is invoked via Docker to ensure reproducible execution environments.

See: https://opm-project.org/
"""

from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any

from ..base import SimulatorAdapter, SimulatorResult, SimulatorError


class OPMFlowAdapter(SimulatorAdapter):
    """Adapter for OPM Flow reservoir simulator.
    
    Runs OPM Flow inside a Docker container, parsing output files
    to determine convergence status and extract metrics.
    
    Args:
        image: Docker image name for OPM Flow (default: "opm-flow:latest")
        timeout: Maximum seconds to wait for simulation (default: 3600)
    """
    
    def __init__(
        self, 
        image: str = "opm-flow:latest",
        timeout: int = 3600,
    ) -> None:
        self._image = image
        self._timeout = timeout
    
    def run(self, case: str) -> SimulatorResult:
        """Execute OPM Flow simulation.
        
        Args:
            case: Path to an ECLIPSE-format .DATA deck file.
        
        Returns:
            SimulatorResult with convergence status and parsed metrics.
        
        Raises:
            SimulatorError: If Docker is unavailable or container fails to start.
        """
        case_path = Path(case)
        
        if not case_path.exists():
            raise SimulatorError(f"Deck file not found: {case}")
        
        # Verify Docker is available
        if not self._docker_available():
            raise SimulatorError(
                "Docker is not available. Ensure Docker is installed and running."
            )
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as output_dir:
            try:
                result = self._run_container(case_path, Path(output_dir))
                return self._parse_results(case_path, Path(output_dir), result)
            except subprocess.TimeoutExpired:
                return SimulatorResult(
                    converged=False,
                    errors=[f"Simulation timeout after {self._timeout}s"],
                    metrics={"timeout": True},
                )
            except subprocess.CalledProcessError as e:
                return SimulatorResult(
                    converged=False,
                    errors=[f"Container execution failed: {e.returncode}"],
                    metrics={"exit_code": e.returncode},
                )
    
    def _docker_available(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _run_container(
        self, 
        case_path: Path, 
        output_dir: Path,
    ) -> subprocess.CompletedProcess:
        """Run OPM Flow container with mounted volumes."""
        data_dir = case_path.parent.resolve()
        case_name = case_path.name
        
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{data_dir}:/simulation/data:ro",
            "-v", f"{output_dir}:/simulation/output",
            self._image,
            "flow", 
            f"data/{case_name}",
            "--output-dir=output/",
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            timeout=self._timeout,
            text=True,
        )
    
    def _parse_results(
        self,
        case_path: Path,
        output_dir: Path,
        result: subprocess.CompletedProcess,
    ) -> SimulatorResult:
        """Parse OPM Flow output to extract convergence and metrics."""
        case_stem = case_path.stem
        prt_file = output_dir / f"{case_stem}.PRT"
        
        errors: list[str] = []
        metrics: dict[str, Any] = {
            "exit_code": result.returncode,
        }
        
        # Check for PRT file (main output)
        if not prt_file.exists():
            errors.append("No .PRT output file generated")
            return SimulatorResult(
                converged=False,
                errors=errors,
                metrics=metrics,
            )
        
        # Parse PRT file for convergence indicators
        prt_content = prt_file.read_text(errors="replace")
        
        # Look for common failure patterns
        if "Error" in prt_content or "ERROR" in prt_content:
            errors.extend(self._extract_errors(prt_content))
        
        if "Linear solve did not converge" in prt_content:
            errors.append("LINEAR_SOLVE_FAILURE")
        
        if "Timestep chopped" in prt_content:
            metrics["timestep_chops"] = prt_content.count("Timestep chopped")
        
        # Check for successful completion
        converged = (
            result.returncode == 0 
            and len(errors) == 0
            and "Simulation complete" in prt_content
        )
        
        # Collect output artifacts
        artifacts = {}
        for suffix in [".PRT", ".EGRID", ".INIT", ".UNRST", ".SMSPEC", ".UNSMRY"]:
            artifact = output_dir / f"{case_stem}{suffix}"
            if artifact.exists():
                artifacts[suffix.lstrip(".")] = str(artifact)
        
        return SimulatorResult(
            converged=converged,
            errors=errors,
            metrics=metrics,
            artifacts=artifacts,
        )
    
    def _extract_errors(self, prt_content: str) -> list[str]:
        """Extract error messages from PRT file content."""
        errors = []
        for line in prt_content.split("\n"):
            line_upper = line.upper()
            if "ERROR" in line_upper and len(line.strip()) < 200:
                errors.append(line.strip())
        return errors[:10]  # Limit to first 10 errors
    
    @property
    def name(self) -> str:
        return f"OPMFlow({self._image})"
