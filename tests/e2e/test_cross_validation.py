"""E2E Cross-Validation: SPE1 + SPE5 (5-spot) — OPM vs MRST

Calls the deployed CLARISSA Sim-Engine (Cloud Run) and validates that
OPM and MRST backends produce consistent results for two benchmark cases.

Issue #131 | MR based on !125 (semantic fixes)
ADR-040 v2 — PAL arch ICE v2.1

Usage (CI):
    E2E=true pytest tests/e2e/test_cross_validation.py -v --tb=short

Usage (manual):
    SIM_ENGINE_URL=https://clarissa-sim-engine-... pytest tests/e2e/ -v
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

import pytest
import requests

# ── Config ─────────────────────────────────────────────────────────────────

SIM_ENGINE_URL = os.environ.get(
    "SIM_ENGINE_URL",
    "https://clarissa-sim-engine-518587440396.europe-north1.run.app",
).rstrip("/")

POLL_INTERVAL_S = 5
POLL_TIMEOUT_S = 180  # 3 min per run
BACKENDS = ["opm", "mrst"]

# Cross-validation tolerances
PRESSURE_TOL_PCT = 15.0    # OPM vs MRST average pressure
SATURATION_TOL_PCT = 20.0  # OPM vs MRST average oil saturation


# ── SPE1 Request (Odeh 1981) ────────────────────────────────────────────────

SPE1_REQUEST = {
    "title": "SPE1 — Odeh Black-Oil Benchmark (E2E)",
    "grid": {
        "nx": 10, "ny": 10, "nz": 3,
        "dx": 152.4, "dy": 152.4, "dz": 6.1,
        "depth_top": 2743.2,   # 9000 ft
        "porosity": 0.3,
        "permeability_x": 500.0,
        "permeability_y": 500.0,
        "permeability_z": 50.0,
    },
    "wells": [
        {
            "name": "INJ1",
            "well_type": "injector",
            "i": 0, "j": 0,
            "k_top": 0, "k_bottom": 2,
            "bhp_bar": 415.0,  # 6000 psia
            "phases": ["gas"],
        },
        {
            "name": "PROD1",
            "well_type": "producer",
            "i": 9, "j": 9,
            "k_top": 0, "k_bottom": 2,
            "bhp_bar": 138.0,  # 2000 psia
            "phases": ["oil", "gas", "water"],
        },
    ],
    "fluid": {
        "oil_density_kg_m3": 785.0,
        "water_density_kg_m3": 1021.0,
        "oil_viscosity_cp": 1.2,
        "water_viscosity_cp": 0.96,
        "initial_pressure_bar": 331.0,  # 4800 psia
        "bubble_point_bar": 248.0,       # 3600 psia
    },
    "timesteps_days": [30, 60, 90, 180, 270, 365],
}


# ── SPE5 Request (5-spot pattern) ───────────────────────────────────────────

SPE5_REQUEST = {
    "title": "SPE5 — 5-Spot Waterflood Benchmark (E2E)",
    "grid": {
        "nx": 9, "ny": 9, "nz": 3,
        "dx": 100.0, "dy": 100.0, "dz": 10.0,
        "depth_top": 2000.0,
        "porosity": 0.2,
        "permeability_x": 200.0,
        "permeability_y": 200.0,
        "permeability_z": 20.0,
    },
    "wells": [
        # 4 corner injectors
        {
            "name": "INJ_SW",
            "well_type": "injector",
            "i": 0, "j": 0,
            "k_top": 0, "k_bottom": 2,
            "rate_m3_day": 50.0,
            "phases": ["water"],
        },
        {
            "name": "INJ_NW",
            "well_type": "injector",
            "i": 0, "j": 8,
            "k_top": 0, "k_bottom": 2,
            "rate_m3_day": 50.0,
            "phases": ["water"],
        },
        {
            "name": "INJ_NE",
            "well_type": "injector",
            "i": 8, "j": 8,
            "k_top": 0, "k_bottom": 2,
            "rate_m3_day": 50.0,
            "phases": ["water"],
        },
        {
            "name": "INJ_SE",
            "well_type": "injector",
            "i": 8, "j": 0,
            "k_top": 0, "k_bottom": 2,
            "rate_m3_day": 50.0,
            "phases": ["water"],
        },
        # Center producer
        {
            "name": "PROD_C",
            "well_type": "producer",
            "i": 4, "j": 4,
            "k_top": 0, "k_bottom": 2,
            "bhp_bar": 150.0,
            "phases": ["oil", "water"],
        },
    ],
    "fluid": {
        "oil_density_kg_m3": 800.0,
        "water_density_kg_m3": 1000.0,
        "oil_viscosity_cp": 2.0,
        "water_viscosity_cp": 0.5,
        "initial_pressure_bar": 250.0,
        "bubble_point_bar": 80.0,
    },
    "timesteps_days": [30, 60, 90, 180, 270, 365],
}


# ── Helpers ────────────────────────────────────────────────────────────────

def submit_job(request_data: dict, backend: str) -> str:
    """Submit a simulation job, return job_id."""
    payload = {**request_data, "backend": backend}
    resp = requests.post(f"{SIM_ENGINE_URL}/sim/run", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_result(job_id: str) -> dict:
    """Poll until job completes, return result dict."""
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        resp = requests.get(f"{SIM_ENGINE_URL}/sim/{job_id}", timeout=15)
        resp.raise_for_status()
        status = resp.json()
        state = status.get("status", "")
        if state == "completed":
            res = requests.get(
                f"{SIM_ENGINE_URL}/sim/{job_id}/result", timeout=30
            )
            res.raise_for_status()
            return res.json()
        elif state in ("failed", "error"):
            logs = requests.get(
                f"{SIM_ENGINE_URL}/sim/{job_id}/logs", timeout=15
            ).text
            pytest.fail(
                f"Job {job_id} failed (backend={status.get('backend','?')})\n"
                f"Logs: {logs[:800]}"
            )
        time.sleep(POLL_INTERVAL_S)

    pytest.fail(f"Job {job_id} timed out after {POLL_TIMEOUT_S}s")


def avg_pressure(result: dict) -> float:
    """Extract average pressure [bar] from last timestep."""
    timesteps = result.get("timesteps", [])
    if not timesteps:
        return float("nan")
    last = timesteps[-1]
    pressures = last.get("cells", {}).get("pressure", [])
    if not pressures:
        return float("nan")
    return sum(pressures) / len(pressures)


def avg_oil_saturation(result: dict) -> float:
    """Extract average oil saturation from last timestep."""
    timesteps = result.get("timesteps", [])
    if not timesteps:
        return float("nan")
    last = timesteps[-1]
    sats = last.get("cells", {}).get("saturation_oil", [])
    if not sats:
        return float("nan")
    return sum(sats) / len(sats)


def pct_diff(a: float, b: float) -> float:
    """% difference relative to mean."""
    mean = (a + b) / 2.0
    if mean == 0:
        return 0.0
    return abs(a - b) / mean * 100.0


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sim_engine_healthy():
    """Assert sim-engine is reachable."""
    resp = requests.get(f"{SIM_ENGINE_URL}/health", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    assert data.get("status") == "healthy", f"Sim-engine unhealthy: {data}"
    assert "opm" in data.get("backends", []), "OPM backend missing"
    assert "mrst" in data.get("backends", []), "MRST backend missing"
    return data


# ── SPE1 Tests ─────────────────────────────────────────────────────────────

class TestSPE1CrossValidation:
    """E2E: SPE1 Odeh 1981 — OPM vs MRST cross-validation."""

    @pytest.fixture(scope="class")
    def spe1_results(self, sim_engine_healthy):
        """Run SPE1 on both backends, return {backend: result}."""
        results = {}
        for backend in BACKENDS:
            job_id = submit_job(SPE1_REQUEST, backend)
            result = poll_result(job_id)
            results[backend] = result
            # Persist for artifact
            with open(f"/tmp/spe1_{backend}_result.json", "w") as f:
                json.dump(result, f, indent=2)
        return results

    def test_spe1_opm_converged(self, spe1_results):
        """SPE1 OPM: simulation converges."""
        r = spe1_results["opm"]
        assert r.get("converged") is True, f"OPM SPE1 not converged: {r}"

    @pytest.mark.xfail(reason="MRST readEclipseDeck rejects WATER keyword in API decks — see Issue #133", strict=False)
    def test_spe1_mrst_converged(self, spe1_results):
        """SPE1 MRST: simulation converges."""
        r = spe1_results["mrst"]
        assert r.get("converged") is True, f"MRST SPE1 not converged: {r}"

    def test_spe1_opm_pressure_range(self, spe1_results):
        """SPE1 OPM: average final pressure within ±50% of reference (331 bar)."""
        p = avg_pressure(spe1_results["opm"])
        ref = 331.0
        assert (
            ref * 0.5 <= p <= ref * 1.5
        ), f"OPM SPE1 pressure out of range: {p:.1f} bar (ref={ref} bar)"

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe1_mrst_pressure_range(self, spe1_results):
        """SPE1 MRST: average final pressure within ±50% of reference (331 bar)."""
        p = avg_pressure(spe1_results["mrst"])
        ref = 331.0
        assert (
            ref * 0.5 <= p <= ref * 1.5
        ), f"MRST SPE1 pressure out of range: {p:.1f} bar (ref={ref} bar)"

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe1_pressure_cross_validation(self, spe1_results):
        """SPE1: OPM vs MRST average pressure within ±15%."""
        p_opm = avg_pressure(spe1_results["opm"])
        p_mrst = avg_pressure(spe1_results["mrst"])
        diff = pct_diff(p_opm, p_mrst)
        assert diff <= PRESSURE_TOL_PCT, (
            f"SPE1 pressure divergence: OPM={p_opm:.2f} bar, "
            f"MRST={p_mrst:.2f} bar, diff={diff:.1f}% > {PRESSURE_TOL_PCT}%"
        )

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe1_saturation_cross_validation(self, spe1_results):
        """SPE1: OPM vs MRST average oil saturation within ±20%."""
        s_opm = avg_oil_saturation(spe1_results["opm"])
        s_mrst = avg_oil_saturation(spe1_results["mrst"])
        diff = pct_diff(s_opm, s_mrst)
        assert diff <= SATURATION_TOL_PCT, (
            f"SPE1 saturation divergence: OPM={s_opm:.3f}, "
            f"MRST={s_mrst:.3f}, diff={diff:.1f}% > {SATURATION_TOL_PCT}%"
        )

    def test_spe1_timestep_count(self, spe1_results):
        """SPE1: both backends return all 6 report timesteps."""
        for backend in BACKENDS:
            ts = spe1_results[backend].get("timesteps", [])
            assert len(ts) == 6, (
                f"SPE1 {backend}: expected 6 timesteps, got {len(ts)}"
            )


# ── SPE5 Tests ─────────────────────────────────────────────────────────────

class TestSPE5CrossValidation:
    """E2E: SPE5 5-spot waterflood — OPM vs MRST cross-validation."""

    @pytest.fixture(scope="class")
    def spe5_results(self, sim_engine_healthy):
        """Run SPE5 on both backends, return {backend: result}."""
        results = {}
        for backend in BACKENDS:
            job_id = submit_job(SPE5_REQUEST, backend)
            result = poll_result(job_id)
            results[backend] = result
            with open(f"/tmp/spe5_{backend}_result.json", "w") as f:
                json.dump(result, f, indent=2)
        return results

    def test_spe5_opm_converged(self, spe5_results):
        """SPE5 OPM: simulation converges."""
        r = spe5_results["opm"]
        assert r.get("converged") is True, f"OPM SPE5 not converged: {r}"

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe5_mrst_converged(self, spe5_results):
        """SPE5 MRST: simulation converges."""
        r = spe5_results["mrst"]
        assert r.get("converged") is True, f"MRST SPE5 not converged: {r}"

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe5_pressure_cross_validation(self, spe5_results):
        """SPE5: OPM vs MRST average pressure within ±15%."""
        p_opm = avg_pressure(spe5_results["opm"])
        p_mrst = avg_pressure(spe5_results["mrst"])
        diff = pct_diff(p_opm, p_mrst)
        assert diff <= PRESSURE_TOL_PCT, (
            f"SPE5 pressure divergence: OPM={p_opm:.2f} bar, "
            f"MRST={p_mrst:.2f} bar, diff={diff:.1f}% > {PRESSURE_TOL_PCT}%"
        )

    @pytest.mark.xfail(reason="MRST WATER keyword bug #133", strict=False)
    def test_spe5_saturation_cross_validation(self, spe5_results):
        """SPE5: OPM vs MRST average oil saturation within ±20%."""
        s_opm = avg_oil_saturation(spe5_results["opm"])
        s_mrst = avg_oil_saturation(spe5_results["mrst"])
        diff = pct_diff(s_opm, s_mrst)
        assert diff <= SATURATION_TOL_PCT, (
            f"SPE5 saturation divergence: OPM={s_opm:.3f}, "
            f"MRST={s_mrst:.3f}, diff={diff:.1f}% > {SATURATION_TOL_PCT}%"
        )

    def test_spe5_5spot_injector_count(self, spe5_results):
        """SPE5: producer well data present in results."""
        for backend in BACKENDS:
            ts = spe5_results[backend].get("timesteps", [])
            if ts:
                wells = ts[-1].get("wells", [])
                # At least the center producer should appear
                assert len(wells) >= 1, (
                    f"SPE5 {backend}: no well data in result"
                )


# ── Summary Report ─────────────────────────────────────────────────────────

def pytest_sessionfinish(session, exitstatus):
    """Write summary JSON for CI artifact."""
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sim_engine_url": SIM_ENGINE_URL,
        "cases": ["SPE1", "SPE5"],
        "backends": BACKENDS,
        "exit_status": exitstatus,
    }
    with open("/tmp/e2e-summary.json", "w") as f:
        json.dump(summary, f, indent=2)
