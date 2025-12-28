import os
from orsa.governance.policy import GovernancePolicy

def test_governance_auto_approve_env():
    g = GovernancePolicy()
    os.environ["ORSA_AUTO_APPROVE"] = "1"
    try:
        assert g.request_approval("Reduce WELL A RATE from 100 to 90") is True
    finally:
        os.environ.pop("ORSA_AUTO_APPROVE", None)
