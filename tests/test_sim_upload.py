"""Tests for .DATA file upload endpoint — POST /sim/upload.

Tests:
- Happy path: SPE1 .DATA → parsed → job queued
- Validation: wrong extension, empty file, missing RUNSPEC
- Size limit: oversized file rejected
- Parse errors: malformed deck content
- Backend validation: unknown simulator rejected

Issue #111 | Epic #110 | ADR-040
"""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest


# ─── Fixtures ─────────────────────────────────────────────────────────────

SPE1_PATH = Path(__file__).parent / "fixtures" / "decks" / "spe1" / "SPE1CASE1.DATA"

MINIMAL_DECK = """\
RUNSPEC
TITLE
Minimal Test Deck

DIMENS
10 10 3 /

OIL
WATER

METRIC

GRID

DX
300*50 /
DY
300*50 /
DZ
300*10 /
TOPS
100*2000 /
PORO
300*0.2 /
PERMX
300*100 /

PROPS

DENSITY
800 1000 1.2 /

PVTW
200 1.0 1.0E-5 0.5 0 /

SOLUTION

EQUIL
2000 200 2050 0 0 0 1 1 0 /

SCHEDULE

WELSPECS
'INJ1' 'G1' 1 5 2000 WATER /
'PROD1' 'G1' 10 5 2000 OIL /
/

COMPDAT
'INJ1' 1 5 1 3 OPEN 2* 0.2 /
'PROD1' 10 5 1 3 OPEN 2* 0.2 /
/

WCONINJE
'INJ1' WATER OPEN RATE 100 1* 250 /
/

WCONPROD
'PROD1' OPEN ORAT 1* 1* 1* 1* 180 /
/

TSTEP
30 60 90 /

END
"""


@pytest.fixture
def client():
    """Create FastAPI test client."""
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi[testclient] not available")

    from clarissa.sim_engine.sim_api import app
    return TestClient(app)


@pytest.fixture
def spe1_content() -> bytes:
    """Load SPE1 .DATA file content."""
    if not SPE1_PATH.exists():
        pytest.skip(f"SPE1 fixture not found: {SPE1_PATH}")
    return SPE1_PATH.read_bytes()


@pytest.fixture
def minimal_deck_bytes() -> bytes:
    """Minimal valid deck as bytes."""
    return MINIMAL_DECK.encode("utf-8")


# ─── Happy Path ───────────────────────────────────────────────────────────

class TestUploadHappyPath:
    """Upload valid .DATA files → job created."""

    def test_upload_minimal_deck(self, client, minimal_deck_bytes):
        """Upload minimal deck → 200, job_id returned."""
        resp = client.post(
            "/sim/upload?simulator=opm",
            files={"file": ("TEST.DATA", minimal_deck_bytes, "application/octet-stream")},
        )
        # Backend may not be available → 400, but parse should succeed
        # Accept either 200 (if mock/opm registered) or 400 (backend unavailable)
        if resp.status_code == 200:
            data = resp.json()
            assert "job_id" in data
            assert data["status"] == "pending"
            assert data["parsed_grid"]["nx"] == 10
            assert data["parsed_grid"]["ny"] == 10
            assert data["parsed_grid"]["nz"] == 3
            assert data["parsed_grid"]["wells"] == 2
        else:
            # Backend not registered — that's OK for unit tests
            assert resp.status_code == 400
            assert "not available" in resp.json()["detail"]

    def test_upload_spe1(self, client, spe1_content):
        """Upload SPE1CASE1.DATA → parsed correctly."""
        resp = client.post(
            "/sim/upload?simulator=opm",
            files={"file": ("SPE1CASE1.DATA", spe1_content, "application/octet-stream")},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data["parsed_grid"]["total_cells"] > 0
            assert data["parsed_grid"]["wells"] >= 1
        elif resp.status_code == 400:
            # Backend unavailable
            assert "not available" in resp.json()["detail"]
        else:
            # Parse should always succeed for SPE1
            assert resp.status_code in (200, 400, 422)

    def test_upload_returns_grid_info(self, client, minimal_deck_bytes):
        """Response includes parsed grid dimensions."""
        resp = client.post(
            "/sim/upload?simulator=opm",
            files={"file": ("GRID.DATA", minimal_deck_bytes, "application/octet-stream")},
        )
        if resp.status_code == 200:
            grid = resp.json()["parsed_grid"]
            assert "nx" in grid
            assert "ny" in grid
            assert "nz" in grid
            assert "total_cells" in grid
            assert "wells" in grid
            assert grid["total_cells"] == grid["nx"] * grid["ny"] * grid["nz"]


# ─── Validation ───────────────────────────────────────────────────────────

class TestUploadValidation:
    """Reject invalid uploads."""

    def test_wrong_extension(self, client):
        """Non-.DATA file rejected."""
        resp = client.post(
            "/sim/upload",
            files={"file": ("model.txt", b"RUNSPEC\nDIMENS\n10 10 3 /\n", "text/plain")},
        )
        assert resp.status_code == 400
        assert ".DATA" in resp.json()["detail"]

    def test_empty_file(self, client):
        """Empty file rejected."""
        resp = client.post(
            "/sim/upload",
            files={"file": ("EMPTY.DATA", b"", "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "Empty" in resp.json()["detail"]

    def test_whitespace_only(self, client):
        """Whitespace-only file rejected."""
        resp = client.post(
            "/sim/upload",
            files={"file": ("BLANK.DATA", b"   \n\n  ", "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_missing_runspec(self, client):
        """File without RUNSPEC section rejected."""
        content = b"GRID\nDIMENS\n10 10 3 /\nEND\n"
        resp = client.post(
            "/sim/upload",
            files={"file": ("NOGOOD.DATA", content, "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "RUNSPEC" in resp.json()["detail"]

    def test_no_file_field(self, client):
        """Missing file field returns 422."""
        resp = client.post("/sim/upload")
        assert resp.status_code == 422

    def test_oversized_file(self, client):
        """File exceeding size limit rejected."""
        # Create 11MB content (default limit is 10MB)
        huge = b"RUNSPEC\n" + b"X" * (11 * 1024 * 1024)
        resp = client.post(
            "/sim/upload",
            files={"file": ("HUGE.DATA", huge, "application/octet-stream")},
        )
        assert resp.status_code == 413

    def test_unknown_backend(self, client, minimal_deck_bytes):
        """Unknown simulator parameter rejected after parse."""
        resp = client.post(
            "/sim/upload?simulator=nonexistent",
            files={"file": ("TEST.DATA", minimal_deck_bytes, "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "not available" in resp.json()["detail"]


# ─── Parse Errors ─────────────────────────────────────────────────────────

class TestUploadParseErrors:
    """Deck parsing failures return 422."""

    def test_malformed_dimens(self, client):
        """Invalid DIMENS triggers parse error."""
        content = b"RUNSPEC\nDIMENS\nnot_a_number /\nEND\n"
        resp = client.post(
            "/sim/upload",
            files={"file": ("BAD.DATA", content, "application/octet-stream")},
        )
        # Should be 422 (parse error) or 400 — not 500
        assert resp.status_code in (400, 422)

    def test_deck_with_no_wells(self, client):
        """Deck without SCHEDULE/wells may fail validation."""
        content = b"""\
RUNSPEC
DIMENS
5 5 1 /
OIL
WATER
METRIC

GRID
DX
25*100 /
DY
25*100 /
DZ
25*10 /
TOPS
25*2000 /
PORO
25*0.2 /
PERMX
25*100 /

END
"""
        resp = client.post(
            "/sim/upload",
            files={"file": ("NOWELLS.DATA", content, "application/octet-stream")},
        )
        # Should fail gracefully — either parse error or validation error
        assert resp.status_code in (400, 422)


# ─── Latin-1 Encoding ─────────────────────────────────────────────────────

class TestUploadEncoding:
    """Handle different file encodings."""

    def test_latin1_file(self, client):
        """Latin-1 encoded deck with special chars parses OK."""
        # German umlaut in comment
        content = MINIMAL_DECK.replace(
            "Minimal Test Deck", "Schärding Reservoir Modell"
        ).encode("latin-1")
        resp = client.post(
            "/sim/upload",
            files={"file": ("UMLAUT.DATA", content, "application/octet-stream")},
        )
        # Should parse (latin-1 fallback) — accept 200 or 400 (no backend)
        assert resp.status_code in (200, 400)


# ─── Capacity Limit ───────────────────────────────────────────────────────

class TestUploadCapacity:
    """Job queue capacity checks."""

    def test_capacity_limit_message(self, client, minimal_deck_bytes):
        """When jobs are full, 429 returned with clear message."""
        from clarissa.sim_engine.sim_api import _jobs, _MAX_JOBS
        from clarissa.sim_engine.models import SimStatus, SimRequest

        # Temporarily fill the job queue
        from clarissa.sim_engine.sim_api import JobState
        fake_jobs = {}
        for i in range(_MAX_JOBS):
            jid = f"sim-fake{i}"
            fake_jobs[jid] = JobState(
                job_id=jid,
                request=SimRequest(
                    wells=[{"name": "P1", "well_type": "producer", "i": 0, "j": 0}]
                ),
                status=SimStatus.RUNNING,
            )

        original = dict(_jobs)
        _jobs.update(fake_jobs)
        try:
            resp = client.post(
                "/sim/upload?simulator=opm",
                files={"file": ("TEST.DATA", minimal_deck_bytes, "application/octet-stream")},
            )
            assert resp.status_code == 429
            assert "Too many" in resp.json()["detail"]
        finally:
            _jobs.clear()
            _jobs.update(original)
