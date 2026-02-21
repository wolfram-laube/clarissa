"""Simulator backends — pluggable reservoir simulation engines."""
from .base import SimulatorBackend
from .registry import register_backend, get_backend, list_backends

__all__ = ["SimulatorBackend", "register_backend", "get_backend", "list_backends"]
