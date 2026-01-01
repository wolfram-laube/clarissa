"""Simulator adapter contract tests.

Verifies that all simulator adapters conform to the contract
defined in docs/simulators/adapter_matrix.md.
"""

import pytest
from clarissa.simulators import MockSimulator, SimulatorAdapter, SimulatorResult


def adapters():
    """Return all available adapters for parametrized testing.
    
    Note: OPMFlowAdapter is excluded from standard CI runs as it requires
    Docker. Use integration tests for OPM-specific validation.
    """
    return [
        ("mock", MockSimulator()),
    ]


@pytest.mark.parametrize("name,sim", adapters())
def test_adapter_inherits_base(name, sim):
    """All adapters must inherit from SimulatorAdapter."""
    assert isinstance(sim, SimulatorAdapter)


@pytest.mark.parametrize("name,sim", adapters())
def test_adapter_has_name(name, sim):
    """All adapters must provide a name property."""
    assert hasattr(sim, "name")
    assert isinstance(sim.name, str)
    assert len(sim.name) > 0


@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_run_contract(name, sim):
    """run() must return dict with required fields."""
    out = sim.run("WELL A RATE 90")
    
    assert isinstance(out, dict)
    
    # Required fields
    assert "converged" in out
    assert isinstance(out["converged"], bool)
    
    assert "errors" in out
    assert isinstance(out["errors"], list)
    for e in out["errors"]:
        assert isinstance(e, str)


@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_converged_semantics(name, sim):
    """Contract: converged=True implies errors=[], and vice versa."""
    ok = sim.run("WELL A RATE 90")
    bad = sim.run("WELL A RATE 100")

    # Successful run
    assert ok["converged"] is True
    assert ok["errors"] == []

    # Failed run
    assert bad["converged"] is False
    assert len(bad["errors"]) >= 1


@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_optional_metrics(name, sim):
    """Optional metrics field, if present, must be a dict."""
    out = sim.run("WELL A RATE 90")
    
    if "metrics" in out:
        assert isinstance(out["metrics"], dict)


@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_optional_artifacts(name, sim):
    """Optional artifacts field, if present, must be a dict of strings."""
    out = sim.run("WELL A RATE 90")
    
    if "artifacts" in out:
        assert isinstance(out["artifacts"], dict)
        for k, v in out["artifacts"].items():
            assert isinstance(k, str)
            assert isinstance(v, str)
