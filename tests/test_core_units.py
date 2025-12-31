import os
from clarissa.governance.policy import GovernancePolicy
from clarissa.simulators.mock import MockSimulator
from clarissa_kernel.core import NativeKernel

def test_governance_requires_approval_rate_change():
    g = GovernancePolicy()
    assert g.requires_approval("Reduce WELL A RATE from 100 to 90") is True
    assert g.requires_approval("Update COMMENT only") is False

def test_mock_simulator_convergence_behavior():
    sim = MockSimulator()
    ok = sim.run("WELL A RATE 90")
    bad = sim.run("WELL A RATE 100")
    assert ok["converged"] is True
    assert bad["converged"] is False
    assert "NONLINEAR_DIVERGENCE" in bad["errors"]

def test_native_kernel_explain():
    k = NativeKernel()
    msg_ok = k.explain("WELL A RATE 90", {"converged": True})
    msg_bad = k.explain("WELL A RATE 100", {"converged": False})
    assert "stabil" in msg_ok.lower()
    assert "diverg" in msg_bad.lower()
