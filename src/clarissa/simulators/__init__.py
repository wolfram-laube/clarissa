"""CLARISSA simulator adapters.

This module provides the interface between CLARISSA and external
reservoir simulators. All adapters implement the SimulatorAdapter
contract defined in base.py.

Available adapters:
    MockSimulator: Deterministic mock for testing (always available)
    OPMFlowAdapter: Open Porous Media Flow simulator (requires Docker)
"""

from .base import SimulatorAdapter, SimulatorResult, SimulatorError
from .mock import MockSimulator

__all__ = [
    "SimulatorAdapter",
    "SimulatorResult", 
    "SimulatorError",
    "MockSimulator",
]
