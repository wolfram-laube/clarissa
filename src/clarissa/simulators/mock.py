"""Mock simulator adapter.

Provides a lightweight, deterministic simulator for testing and CI.
Does not perform physically meaningful calculations.
"""

from __future__ import annotations

from .base import SimulatorAdapter, SimulatorResult


class MockSimulator(SimulatorAdapter):
    """Mock simulator for testing CLARISSA's learning loop.
    
    Behavior:
        - Returns converged=True if input contains "RATE 90"
        - Returns converged=False with errors otherwise
    
    This allows deterministic testing of the feedback cycle without
    requiring actual reservoir simulation infrastructure.
    """
    
    def run(self, case: str) -> SimulatorResult:
        """Execute mock simulation based on simple pattern matching."""
        stable = "RATE 90" in case
        
        if stable:
            return SimulatorResult(
                converged=True,
                errors=[],
                metrics={"timestep_collapses": 0},
            )
        else:
            return SimulatorResult(
                converged=False,
                errors=["NONLINEAR_DIVERGENCE"],
                metrics={"timestep_collapses": 3},
            )
