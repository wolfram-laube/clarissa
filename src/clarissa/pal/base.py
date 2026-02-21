"""PAL — Platform Adapter Layer.

Unified ABC for all pluggable adapters: simulators, evidence providers,
event buses, and future extensions. Each adapter has a name, type, and
standard health/info interface.

ADR-040 | ICE v2.1 §3.2.12 | Issue #172
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PlatformAdapter(ABC):
    """Base class for all platform adapters.

    Subclasses define `adapter_type` as a class variable and implement
    `name`, `healthy()`, and `info()`.
    """

    adapter_type: str = "generic"  # Override in subclasses

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name within this adapter_type (e.g. 'weather', 'opm')."""
        ...

    def healthy(self) -> bool:
        """Return True if this adapter is operational. Override for real checks."""
        return True

    def info(self) -> dict[str, Any]:
        """Return adapter metadata for /health and discovery endpoints."""
        return {
            "name": self.name,
            "adapter_type": self.adapter_type,
            "healthy": self.healthy(),
        }
