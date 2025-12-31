import pytest
from clarissa.simulators.mock import MockSimulator

def adapters():
    # Add future adapters here (MRST, OPM) once implemented.
    return [
        ("mock", MockSimulator()),
    ]

@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_run_contract(name, sim):
    out = sim.run("WELL A RATE 90")
    assert isinstance(out, dict)
    assert "converged" in out
    assert isinstance(out["converged"], bool)
    assert "errors" in out
    assert isinstance(out["errors"], list)
    for e in out["errors"]:
        assert isinstance(e, str)

@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_converged_semantics(name, sim):
    ok = sim.run("WELL A RATE 90")
    bad = sim.run("WELL A RATE 100")

    assert ok["converged"] is True
    assert ok["errors"] == []

    assert bad["converged"] is False
    assert len(bad["errors"]) >= 1
