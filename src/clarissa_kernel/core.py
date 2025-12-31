"""CLARISSA Native Simulation Kernel (mock).

This is a laboratory environment for controlled experiments, explainability,
and learning signal generation. It is not intended to replace production simulators.
"""

from __future__ import annotations
from typing import Any


class NativeKernel:
    def explain(self, deck_text: str, outcome: dict[str, Any]) -> str:
        if outcome.get("converged"):
            return "Simulation stabilized after rate reduction; no divergence flags were observed."
        return "Simulation did not converge; timestep collapse and nonlinear divergence flags persist."
