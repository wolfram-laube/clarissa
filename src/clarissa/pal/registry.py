"""PAL AdapterRegistry — Unified adapter registration and discovery.

All adapters (simulators, evidence providers, event buses) register
here and can be discovered by type + name.

ADR-040 | Issue #172
"""
from __future__ import annotations

import logging
from typing import TypeVar

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=PlatformAdapter)


class AdapterRegistry:
    """Central registry for all platform adapters.

    Usage:
        registry = AdapterRegistry()
        registry.register(WeatherProvider())
        registry.register(OPMBackend())

        provider = registry.get("evidence", "weather")
        backends = registry.list("simulator")
        health = registry.health()
    """

    def __init__(self) -> None:
        self._adapters: dict[str, dict[str, PlatformAdapter]] = {}

    def register(self, adapter: PlatformAdapter) -> None:
        """Register an adapter. Overwrites existing with same type+name."""
        atype = adapter.adapter_type
        if atype not in self._adapters:
            self._adapters[atype] = {}
        self._adapters[atype][adapter.name] = adapter
        logger.info(f"PAL: registered {atype}/{adapter.name}")

    def get(self, adapter_type: str, name: str) -> PlatformAdapter:
        """Get adapter by type and name. Raises KeyError with helpful message."""
        bucket = self._adapters.get(adapter_type, {})
        if name not in bucket:
            available = list(bucket.keys()) or ["(none)"]
            raise KeyError(
                f"No {adapter_type} adapter named '{name}'. "
                f"Available: {', '.join(available)}"
            )
        return bucket[name]

    def list(self, adapter_type: str) -> list[PlatformAdapter]:
        """List all adapters of a given type."""
        return list(self._adapters.get(adapter_type, {}).values())

    def list_names(self, adapter_type: str) -> list[str]:
        """List adapter names for a given type."""
        return list(self._adapters.get(adapter_type, {}).keys())

    def health(self) -> dict:
        """Health check for all registered adapters."""
        result = {"healthy": True, "adapters": {}}
        for atype, bucket in self._adapters.items():
            result["adapters"][atype] = {}
            for name, adapter in bucket.items():
                try:
                    ok = adapter.healthy()
                except Exception as e:
                    logger.warning(f"Health check failed for {atype}/{name}: {e}")
                    ok = False
                result["adapters"][atype][name] = ok
                if not ok:
                    result["healthy"] = False
        return result

    def info(self) -> list[dict]:
        """Info for all registered adapters."""
        return [
            adapter.info()
            for bucket in self._adapters.values()
            for adapter in bucket.values()
        ]

    def __len__(self) -> int:
        return sum(len(b) for b in self._adapters.values())

    def __repr__(self) -> str:
        counts = {k: len(v) for k, v in self._adapters.items()}
        return f"AdapterRegistry({counts})"
