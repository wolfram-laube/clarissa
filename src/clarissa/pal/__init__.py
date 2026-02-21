"""PAL — Platform Adapter Layer.

Unified foundation for pluggable adapters.
"""
from .base import PlatformAdapter
from .registry import AdapterRegistry

__all__ = ["PlatformAdapter", "AdapterRegistry"]
