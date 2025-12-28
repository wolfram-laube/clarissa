"""ORSA Agent (prototype).

This skeleton demonstrates the architectural separation:
- LLM reasoning: stubbed (explain/plan as strings)
- RL: stubbed (selects an action sequence)
- Governance: explicit gate before applying changes
- Simulator/Kernal: mock backends
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any


class Simulator(Protocol):
    def run(self, deck_text: str) -> dict[str, Any]: ...


class Kernel(Protocol):
    def explain(self, deck_text: str, outcome: dict[str, Any]) -> str: ...


class Governance(Protocol):
    def requires_approval(self, proposal: str) -> bool: ...
    def request_approval(self, proposal: str) -> bool: ...


@dataclass
class ORSAAgent:
    governance: Governance
    simulator: Simulator
    kernel: Kernel

    def demo(self) -> dict[str, Any]:
        deck = """-- minimal deck (mock)
WELL A RATE 100
"""
        print("[ORSA] Starting demo with deck:\n", deck)

        # "RL" proposes an action sequence (stubbed)
        proposal = "Reduce WELL A RATE from 100 to 90 to improve stability"
        print("[ORSA/RL] Proposal:", proposal)

        # Governance gate
        if self.governance.requires_approval(proposal):
            approved = self.governance.request_approval(proposal)
            if not approved:
                print("[ORSA/GOV] Proposal denied. Exiting.")
                return {"ran": False, "denied": True}

        # Apply change (trivial edit)
        new_deck = deck.replace("RATE 100", "RATE 90")
        print("[ORSA] Applying change and running simulator...")

        outcome = self.simulator.run(new_deck)
        explanation = self.kernel.explain(new_deck, outcome)

        print("[SIM] Outcome:", outcome)
        print("[ORSA/LLM] Explanation:", explanation)
        return outcome
