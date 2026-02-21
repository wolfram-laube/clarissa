"""SimulatorBackend ABC — Base class for all reservoir simulator backends.

Each backend knows how to:
1. Validate simulation parameters
2. Run a simulation (async with progress callback)
3. Parse raw output into UnifiedResult

Implementations: OPMBackend, MRSTBackend (future), MockBackend (testing)

Issue #162 | Epic #161 | ADR-038
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Callable, Optional

from clarissa.pal import PlatformAdapter
from clarissa.sim_engine.models import (
    SimRequest,
    UnifiedResult,
    SimMetadata,
    SimStatus,
)


class SimulatorBackend(PlatformAdapter):
    """ABC for reservoir simulator backends.

    Subclasses must implement:
    - name: unique backend identifier (e.g. "opm", "mrst")
    - validate(request): check if request is valid for this backend
    - run(request, on_progress): execute simulation
    - parse_result(raw, request): convert raw output to UnifiedResult

    The run() method should call on_progress(pct) periodically
    with percentage 0-100 for real-time progress tracking.
    """

    adapter_type: str = "simulator"

    @abstractmethod
    def validate(self, request: SimRequest) -> list[str]:
        """Validate simulation parameters for this backend.

        Returns:
            List of validation error messages (empty = valid).
        """
        ...

    @abstractmethod
    def run(
        self,
        request: SimRequest,
        work_dir: str,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> dict[str, Any]:
        """Run the simulation.

        Args:
            request: Validated simulation request.
            work_dir: Directory for input/output files.
            on_progress: Optional callback, called with pct 0-100.

        Returns:
            Raw result dict (backend-specific). Passed to parse_result().

        Raises:
            RuntimeError: If simulation fails.
        """
        ...

    @abstractmethod
    def parse_result(
        self,
        raw: dict[str, Any],
        request: SimRequest,
    ) -> UnifiedResult:
        """Parse raw simulator output into UnifiedResult.

        Args:
            raw: Backend-specific output from run().
            request: Original simulation request (for context).

        Returns:
            Standardized UnifiedResult.
        """
        ...

    @property
    def version(self) -> str:
        """Return backend version string. Override for real detection."""
        return "unknown"

    def info(self) -> dict[str, Any]:
        """Extended info with version."""
        base = super().info()
        base["version"] = self.version
        return base
