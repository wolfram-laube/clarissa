"""Simulator Backend Registry.

Manages registered simulator backends (OPM, MRST, etc.).
Uses the PAL AdapterRegistry under the hood.

Issue #162 | Epic #161
"""
from __future__ import annotations

import logging
from typing import Optional

from clarissa.pal import AdapterRegistry
from .base import SimulatorBackend

logger = logging.getLogger(__name__)

_registry: Optional[AdapterRegistry] = None


def get_registry() -> AdapterRegistry:
    """Get or create the simulator backend registry."""
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
        _register_builtins(_registry)
    return _registry


def _register_builtins(registry: AdapterRegistry) -> None:
    """Register built-in simulator backends.

    Currently empty — OPM and MRST are registered when their
    modules are imported (issues #163, #166).
    """
    logger.info("Simulator backend registry initialized (no built-ins yet)")


def register_backend(backend: SimulatorBackend) -> None:
    """Register a simulator backend."""
    get_registry().register(backend)


def get_backend(name: str) -> SimulatorBackend:
    """Get simulator backend by name."""
    return get_registry().get("simulator", name)


def list_backends() -> list[str]:
    """List registered backend names."""
    return get_registry().list_names("simulator")
