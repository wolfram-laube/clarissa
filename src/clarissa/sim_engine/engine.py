"""SimEngine — Thin SDK convenience wrapper.

Composes independent modules for notebook/REPL convenience.
NOT the architectural core — that's the PAL Registry + independent modules.

For production code and services, use the modules directly:
    from clarissa.sim_engine.backends.registry import get_backend
    from clarissa.sim_engine.comparison import compare
    from clarissa.sim_engine.deck_parser import parse_deck_file, deck_to_sim_request
    from clarissa.sim_engine.eclipse_reader import read_eclipse_output
    from clarissa.sim_engine.deck_generator import generate_deck

SimEngine is syntactic sugar for interactive use:
    engine = SimEngine()
    result = engine.run(request, backend="opm")
    report = engine.compare(result_a, result_b)

It holds NO state beyond a reference to the PAL AdapterRegistry.
All business logic lives in the modules it delegates to.

ADR-040 | Epic #161
"""
from __future__ import annotations

import logging
import tempfile
from typing import Any, Callable, Optional

from clarissa.pal import AdapterRegistry
from clarissa.sim_engine.backends.base import SimulatorBackend
from clarissa.sim_engine.backends.registry import get_registry
from clarissa.sim_engine.comparison import ComparisonReport, compare
from clarissa.sim_engine.models import SimRequest, SimStatus, UnifiedResult

logger = logging.getLogger(__name__)


class SimEngine:
    """Thin convenience wrapper over PAL Registry + independent modules.

    Delegates to:
        - PAL AdapterRegistry for backend management
        - comparison.compare() for cross-validation
        - deck_parser for .DATA parsing
        - eclipse_reader for output reading
        - deck_generator for .DATA generation

    For services (sim_api.py), use the modules and registry directly.
    """

    def __init__(self, registry: Optional[AdapterRegistry] = None) -> None:
        self._registry = registry if registry is not None else get_registry()

    # ─── Backend Management (delegates to PAL Registry) ───────────

    def register(self, backend: SimulatorBackend) -> None:
        """Register a backend in the PAL Registry."""
        self._registry.register(backend)

    def get_backend(self, name: str) -> SimulatorBackend:
        """Get backend from PAL Registry."""
        return self._registry.get("simulator", name)

    @property
    def backends(self) -> list[str]:
        return self._registry.list_names("simulator")

    # ─── Convenience: run ─────────────────────────────────────────

    def run(
        self,
        request: SimRequest,
        backend: Optional[str] = None,
        work_dir: Optional[str] = None,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> UnifiedResult:
        """Validate → run → parse. Convenience for notebooks."""
        name = backend or request.backend or self.backends[0]
        b = self.get_backend(name)

        errors = b.validate(request)
        if errors:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")

        wd = work_dir or tempfile.mkdtemp(prefix=f"clarissa-{name}-")
        try:
            raw = b.run(request, wd, on_progress=on_progress)
            raw.setdefault("job_id", f"{name}-local")
            return b.parse_result(raw, request)
        except Exception as e:
            logger.error(f"Simulation failed on '{name}': {e}")
            raise

    # ─── Convenience: compare (delegates to comparison module) ────

    def compare(
        self,
        result_a: UnifiedResult,
        result_b: UnifiedResult,
        label_a: Optional[str] = None,
        label_b: Optional[str] = None,
    ) -> ComparisonReport:
        """Delegates to comparison.compare()."""
        return compare(
            result_a, result_b,
            label_a or result_a.metadata.backend,
            label_b or result_b.metadata.backend,
        )

    # ─── Convenience: I/O (delegates to independent modules) ──────

    def read_output(self, case_path: str, **kwargs) -> UnifiedResult:
        """Delegates to eclipse_reader.read_eclipse_output()."""
        from clarissa.sim_engine.eclipse_reader import read_eclipse_output
        return read_eclipse_output(case_path, **kwargs)

    def parse_deck(self, deck_path: str) -> SimRequest:
        """Delegates to deck_parser."""
        from clarissa.sim_engine.deck_parser import parse_deck_file, deck_to_sim_request
        return deck_to_sim_request(parse_deck_file(deck_path))

    def generate_deck(self, request: SimRequest) -> str:
        """Delegates to deck_generator."""
        from clarissa.sim_engine.deck_generator import generate_deck
        return generate_deck(request)

    # ─── Introspection (delegates to PAL Registry) ────────────────

    def health(self) -> dict[str, Any]:
        """Delegates to registry.health()."""
        return self._registry.health()
