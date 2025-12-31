"""Neuro-symbolic governance (prototype).

In a real system this would encode rules, constraints, escalation thresholds,
and approval requirements. Here we implement a simple approval gate.
"""

from __future__ import annotations


import os


class GovernancePolicy:
    def requires_approval(self, proposal: str) -> bool:
        # Prototype rule: any change that alters rates requires approval
        return "RATE" in proposal.upper() or "rate" in proposal

    def request_approval(self, proposal: str) -> bool:
        """Request human approval.

        If AUTO_APPROVE=1 is set, approvals are auto-granted (CI-friendly).
        """
        if os.getenv("AUTO_APPROVE", "0").strip() == "1":
            print("[GOV] Auto-approve enabled (AUTO_APPROVE=1).")
            return True
        print("[GOV] Approval required for:")
        print("      ", proposal)
        resp = input("Approve? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
