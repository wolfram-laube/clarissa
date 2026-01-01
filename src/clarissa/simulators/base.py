"""Base class for simulator adapters.

Defines the contract that all simulator backends must implement.
See docs/simulators/adapter_matrix.md for detailed specifications.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TypedDict


class SimulatorResult(TypedDict, total=False):
    """Result structure returned by simulator adapters.
    
    Required fields:
        converged: Whether the simulation completed successfully.
        errors: List of error messages (empty if converged).
    
    Optional fields:
        metrics: Numerical metrics from the simulation run.
        artifacts: Paths or identifiers for output files.
    """
    converged: bool
    errors: list[str]
    metrics: dict[str, float | int | str]
    artifacts: dict[str, str]


class SimulatorAdapter(ABC):
    """Abstract base class for simulator adapters.
    
    All simulator backends (MockSimulator, OPMFlowAdapter, MRSTAdapter, etc.)
    must implement this interface to participate in CLARISSA's learning loop.
    
    Contract semantics:
        - If converged is False, errors MUST be non-empty.
        - If converged is True, errors MUST be empty.
    """
    
    @abstractmethod
    def run(self, case: str) -> SimulatorResult:
        """Execute a simulation case and return structured results.
        
        Args:
            case: The simulation input. For file-based simulators, this is
                  typically a path to a deck file or the deck content itself.
        
        Returns:
            SimulatorResult with at minimum 'converged' and 'errors' fields.
        
        Raises:
            SimulatorError: If the simulator cannot be invoked at all
                           (distinct from simulation non-convergence).
        """
        ...
    
    @property
    def name(self) -> str:
        """Human-readable name for this simulator backend."""
        return self.__class__.__name__


class SimulatorError(Exception):
    """Raised when a simulator cannot be invoked.
    
    This is distinct from simulation non-convergence. Non-convergence is
    reported via the SimulatorResult structure. SimulatorError indicates
    infrastructure-level failures (e.g., Docker not running, missing files).
    """
    pass
