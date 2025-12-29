"""Mock simulator adapter.

Represents simulator-in-the-loop feedback. Replace with real adapters later.
"""

from __future__ import annotations
from typing import Any


class MockSimulator:
    def run(self, deck_text: str) -> dict[str, Any]:
        # Minimal "numerical" outcome
        stable = "RATE 90" in deck_text
        return {
            "ran": True,
            "converged": stable,
            "timestep_collapses": 0 if stable else 3,
            "errors": [] if stable else ["NONLINEAR_DIVERGENCE"],
        }
