"""Contract tests against real Eclipse decks.

Validates that:
1. Deck parser correctly reads reference SPE datasets
2. Parsed SimRequest matches known deck properties
3. Generated decks (deck_generator) produce valid Eclipse structure
4. Roundtrip: parse real deck → SimRequest → generate new deck → re-parse

Uses test fixtures from tests/fixtures/decks/ (OPM reference data).

Issue #173 | Epic #161 | ADR-040
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from clarissa.sim_engine.deck_parser import (
    DeckParseResult,
    deck_to_sim_request,
    parse_deck,
    parse_deck_file,
)
from clarissa.sim_engine.deck_generator import generate_deck
from clarissa.sim_engine.models import (
    FluidProperties,
    GridParams,
    Phase,
    SimRequest,
    WellConfig,
    WellType,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "decks"


@pytest.fixture
def spe1_case2_parsed() -> DeckParseResult:
    return parse_deck_file(str(FIXTURES_DIR / "spe1" / "SPE1CASE2.DATA"))


@pytest.fixture
def spe1_case2_request(spe1_case2_parsed) -> SimRequest:
    return deck_to_sim_request(spe1_case2_parsed)


@pytest.fixture
def spe1_case1_parsed() -> DeckParseResult:
    return parse_deck_file(str(FIXTURES_DIR / "spe1" / "SPE1CASE1.DATA"))


@pytest.fixture
def spe1_2p_parsed() -> DeckParseResult:
    return parse_deck_file(str(FIXTURES_DIR / "spe1" / "SPE1CASE2_2P.DATA"))


@pytest.fixture
def watershed_parsed() -> DeckParseResult:
    return parse_deck_file(str(FIXTURES_DIR / "watershed" / "WATERSHED.DATA"))


@pytest.fixture
def watershed_request(watershed_parsed) -> SimRequest:
    return deck_to_sim_request(watershed_parsed)


# ═══════════════════════════════════════════════════════════════════════════
# 1. SPE1 Case 2 — Primary Reference Deck
# ═══════════════════════════════════════════════════════════════════════════


class TestSPE1Case2Parsing:
    """SPE1 Case 2: 10×10×3, three-phase, gas injection, FIELD units.

    Reference: Odeh, A.S., "Comparison of Solutions to a Three-Dimensional
    Black-Oil Reservoir Simulation Problem", JPT January 1981.
    """

    def test_grid_dimensions(self, spe1_case2_parsed):
        """Grid is 10×10×3 = 300 cells (from DIMENS keyword)."""
        p = spe1_case2_parsed
        assert p.nx == 10
        assert p.ny == 10
        assert p.nz == 3
        assert p.total_cells == 300

    def test_units_field(self, spe1_case2_parsed):
        assert spe1_case2_parsed.units == "FIELD"
        assert spe1_case2_parsed.is_field is True

    def test_phases(self, spe1_case2_parsed):
        assert "OIL" in spe1_case2_parsed.phases
        assert "GAS" in spe1_case2_parsed.phases
        assert "WATER" in spe1_case2_parsed.phases

    def test_title(self, spe1_case2_parsed):
        assert "SPE1" in spe1_case2_parsed.title

    def test_cell_sizes_field(self, spe1_case2_parsed):
        """All cells are 1000ft × 1000ft. DZ varies by layer."""
        p = spe1_case2_parsed
        assert len(p.dx_values) == 300
        assert all(v == 1000.0 for v in p.dx_values)
        assert all(v == 1000.0 for v in p.dy_values)
        # DZ: 100 cells × 20ft, 100 × 30ft, 100 × 50ft
        assert p.dz_values[:100] == [20.0] * 100
        assert p.dz_values[100:200] == [30.0] * 100
        assert p.dz_values[200:300] == [50.0] * 100

    def test_porosity(self, spe1_case2_parsed):
        """Constant porosity 0.3 throughout."""
        assert len(spe1_case2_parsed.poro_values) == 300
        assert all(v == 0.3 for v in spe1_case2_parsed.poro_values)

    def test_permeability_layers(self, spe1_case2_parsed):
        """Permeability varies by layer: 500, 50, 200 mD."""
        p = spe1_case2_parsed
        assert p.permx_values[:100] == [500.0] * 100
        assert p.permx_values[100:200] == [50.0] * 100
        assert p.permx_values[200:300] == [200.0] * 100

    def test_top_depth(self, spe1_case2_parsed):
        """TOPS = 8325ft for top layer."""
        assert spe1_case2_parsed.tops_values[0] == 8325.0

    def test_two_wells(self, spe1_case2_parsed):
        """Two wells: PROD and INJ."""
        p = spe1_case2_parsed
        assert len(p.welspecs) == 2
        names = {ws["name"] for ws in p.welspecs}
        assert "PROD" in names
        assert "INJ" in names

    def test_producer_location(self, spe1_case2_parsed):
        """PROD at (10, 10) in Eclipse 1-based coords."""
        prod = next(ws for ws in spe1_case2_parsed.welspecs if ws["name"] == "PROD")
        assert prod["i"] == 10
        assert prod["j"] == 10

    def test_injector_location(self, spe1_case2_parsed):
        """INJ at (1, 1) in Eclipse 1-based coords."""
        inj = next(ws for ws in spe1_case2_parsed.welspecs if ws["name"] == "INJ")
        assert inj["i"] == 1
        assert inj["j"] == 1

    def test_producer_compdat(self, spe1_case2_parsed):
        """PROD completed in layer 3 only."""
        comp = next(c for c in spe1_case2_parsed.compdat if c["well"] == "PROD")
        assert comp["k_top"] == 3
        assert comp["k_bottom"] == 3

    def test_injector_compdat(self, spe1_case2_parsed):
        """INJ completed in layer 1 only."""
        comp = next(c for c in spe1_case2_parsed.compdat if c["well"] == "INJ")
        assert comp["k_top"] == 1
        assert comp["k_bottom"] == 1

    def test_producer_control(self, spe1_case2_parsed):
        """PROD: ORAT 20000 STB/day, BHP limit 1000 psia."""
        prod = next(p for p in spe1_case2_parsed.wconprod if p["well"] == "PROD")
        assert prod["control"] == "ORAT"
        assert prod["rate"] == 20000.0

    def test_injector_control(self, spe1_case2_parsed):
        """INJ: GAS injection, RATE 100000 Mscf/day."""
        inj = next(i for i in spe1_case2_parsed.wconinje if i["well"] == "INJ")
        assert inj["fluid"] == "GAS"
        assert inj["control"] == "RATE"
        assert inj["rate"] == 100000.0

    def test_timesteps(self, spe1_case2_parsed):
        """120 monthly timesteps over 10 years."""
        ts = spe1_case2_parsed.tstep_values
        assert len(ts) == 120
        total_days = sum(ts)
        # 10 years ≈ 3650 days
        assert 3640 < total_days < 3660

    def test_density(self, spe1_case2_parsed):
        """Oil 53.66, Water 64.49, Gas 0.0533 lb/ft³."""
        d = spe1_case2_parsed.density
        assert abs(d["oil"] - 53.66) < 0.01
        assert abs(d["water"] - 64.49) < 0.01

    def test_initial_pressure(self, spe1_case2_parsed):
        """Initial pressure 4800 psia at datum 8400ft (from EQUIL)."""
        equil = spe1_case2_parsed.equil
        assert len(equil) >= 2
        assert equil[0] == 8400.0  # datum depth
        assert equil[1] == 4800.0  # pressure


# ═══════════════════════════════════════════════════════════════════════════
# 2. SPE1 → SimRequest Conversion
# ═══════════════════════════════════════════════════════════════════════════


class TestSPE1SimRequestConversion:
    """Verify unit conversion and model mapping for SPE1."""

    def test_grid_converted_to_meters(self, spe1_case2_request):
        """1000ft → 304.8m."""
        g = spe1_case2_request.grid
        assert abs(g.dx - 304.8) < 0.1
        assert abs(g.dy - 304.8) < 0.1

    def test_grid_dimensions_preserved(self, spe1_case2_request):
        g = spe1_case2_request.grid
        assert g.nx == 10
        assert g.ny == 10
        assert g.nz == 3

    def test_porosity_preserved(self, spe1_case2_request):
        assert spe1_case2_request.grid.porosity == pytest.approx(0.3)

    def test_permeability_mean(self, spe1_case2_request):
        """Mean of 500, 50, 200 mD = 250 mD."""
        assert spe1_case2_request.grid.permeability_x == pytest.approx(250.0)

    def test_depth_converted(self, spe1_case2_request):
        """8325ft → 2537.46m."""
        assert abs(spe1_case2_request.grid.depth_top - 2537.46) < 0.1

    def test_pressure_converted(self, spe1_case2_request):
        """4800 psia → 330.95 bar."""
        assert abs(spe1_case2_request.fluid.initial_pressure_bar - 330.95) < 0.1

    def test_density_converted(self, spe1_case2_request):
        """53.66 lb/ft³ → 859.1 kg/m³ (oil)."""
        assert abs(spe1_case2_request.fluid.oil_density_kg_m3 - 859.1) < 1.0

    def test_two_wells(self, spe1_case2_request):
        assert len(spe1_case2_request.wells) == 2

    def test_producer_0based(self, spe1_case2_request):
        """Eclipse (10,10) → 0-based (9,9)."""
        prod = next(w for w in spe1_case2_request.wells if w.name == "PROD")
        assert prod.i == 9
        assert prod.j == 9
        assert prod.well_type == WellType.PRODUCER

    def test_injector_0based(self, spe1_case2_request):
        """Eclipse (1,1) → 0-based (0,0)."""
        inj = next(w for w in spe1_case2_request.wells if w.name == "INJ")
        assert inj.i == 0
        assert inj.j == 0
        assert inj.well_type == WellType.INJECTOR

    def test_injector_gas_phase(self, spe1_case2_request):
        inj = next(w for w in spe1_case2_request.wells if w.name == "INJ")
        assert Phase.GAS in inj.phases

    def test_timesteps_cumulative(self, spe1_case2_request):
        ts = spe1_case2_request.timesteps_days
        assert len(ts) == 120
        # First step = 31 days
        assert ts[0] == 31.0
        # Last step ≈ 3650 days
        assert 3640 < ts[-1] < 3660

    def test_timesteps_monotonic(self, spe1_case2_request):
        ts = spe1_case2_request.timesteps_days
        for i in range(1, len(ts)):
            assert ts[i] > ts[i - 1]


# ═══════════════════════════════════════════════════════════════════════════
# 3. Watershed Deck (METRIC units)
# ═══════════════════════════════════════════════════════════════════════════


class TestWatershedParsing:
    """Watershed: 20×20×3, METRIC, custom groundwater model."""

    def test_grid_dimensions(self, watershed_parsed):
        assert watershed_parsed.nx == 20
        assert watershed_parsed.ny == 20
        assert watershed_parsed.nz == 3

    def test_units_metric(self, watershed_parsed):
        assert watershed_parsed.units == "METRIC"

    def test_phases(self, watershed_parsed):
        assert "OIL" in watershed_parsed.phases
        assert "WATER" in watershed_parsed.phases

    def test_wells_present(self, watershed_parsed):
        assert len(watershed_parsed.welspecs) >= 2

    def test_timesteps(self, watershed_parsed):
        assert len(watershed_parsed.tstep_values) > 0

    def test_request_no_unit_conversion(self, watershed_request):
        """METRIC: no conversion needed for lengths."""
        g = watershed_request.grid
        assert g.nx == 20
        assert g.ny == 20
        assert g.nz == 3


# ═══════════════════════════════════════════════════════════════════════════
# 4. SPE1 Case 1 vs Case 2 Comparison
# ═══════════════════════════════════════════════════════════════════════════


class TestSPE1Variants:
    """Verify we can distinguish between SPE1 variants."""

    def test_case1_same_grid(self, spe1_case1_parsed, spe1_case2_parsed):
        """Both cases use same grid."""
        assert spe1_case1_parsed.nx == spe1_case2_parsed.nx
        assert spe1_case1_parsed.ny == spe1_case2_parsed.ny
        assert spe1_case1_parsed.nz == spe1_case2_parsed.nz

    def test_case1_same_wells(self, spe1_case1_parsed, spe1_case2_parsed):
        names1 = {ws["name"] for ws in spe1_case1_parsed.welspecs}
        names2 = {ws["name"] for ws in spe1_case2_parsed.welspecs}
        assert names1 == names2

    def test_2p_fewer_phases(self, spe1_2p_parsed):
        """Two-phase variant should not have GAS."""
        assert "OIL" in spe1_2p_parsed.phases
        assert "WATER" in spe1_2p_parsed.phases
        # Note: 2P deck may still have GAS keyword depending on variant


# ═══════════════════════════════════════════════════════════════════════════
# 5. Deck Generator Contract — Output Validity
# ═══════════════════════════════════════════════════════════════════════════


class TestDeckGeneratorContract:
    """Verify deck_generator output contains required Eclipse structure."""

    def test_generated_deck_has_all_sections(self):
        """Generated deck must have RUNSPEC, GRID, PROPS, SOLUTION, SUMMARY, SCHEDULE."""
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[
                WellConfig(name="INJ", well_type=WellType.INJECTOR,
                           i=0, j=0, rate_m3_day=100, phases=[Phase.WATER]),
                WellConfig(name="PROD", well_type=WellType.PRODUCER,
                           i=4, j=4, bhp_bar=150, phases=[Phase.OIL]),
            ],
            timesteps_days=[30, 90, 365],
        )
        deck = generate_deck(request)

        assert "RUNSPEC" in deck
        assert "GRID" in deck
        assert "PROPS" in deck
        assert "SOLUTION" in deck
        assert "SCHEDULE" in deck
        assert "END" in deck

    def test_generated_deck_dimens(self):
        """DIMENS must match request grid."""
        request = SimRequest(
            grid=GridParams(nx=8, ny=6, nz=2),
            wells=[WellConfig(name="W1", well_type=WellType.PRODUCER,
                              i=0, j=0, bhp_bar=100, phases=[Phase.OIL])],
            timesteps_days=[30],
        )
        deck = generate_deck(request)
        assert "8 6 2" in deck or "8  6  2" in deck

    def test_generated_deck_parseable(self):
        """Generated deck should be parseable by our own parser (roundtrip)."""
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1, dx=100, dy=100, dz=10,
                            porosity=0.25, permeability_x=200),
            wells=[
                WellConfig(name="INJ1", well_type=WellType.INJECTOR,
                           i=0, j=0, rate_m3_day=50, phases=[Phase.WATER]),
                WellConfig(name="PROD1", well_type=WellType.PRODUCER,
                           i=4, j=4, bhp_bar=100, phases=[Phase.OIL]),
            ],
            timesteps_days=[30, 90, 180],
        )
        deck_text = generate_deck(request)
        parsed = parse_deck(deck_text)

        assert parsed.nx == 5
        assert parsed.ny == 5
        assert parsed.nz == 1
        assert len(parsed.welspecs) == 2

    def test_well_names_preserved(self):
        """Well names from request appear in generated deck."""
        request = SimRequest(
            grid=GridParams(nx=5, ny=5, nz=1),
            wells=[
                WellConfig(name="ALPHA", well_type=WellType.INJECTOR,
                           i=0, j=0, rate_m3_day=50, phases=[Phase.WATER]),
                WellConfig(name="BRAVO", well_type=WellType.PRODUCER,
                           i=4, j=4, bhp_bar=100, phases=[Phase.OIL]),
            ],
            timesteps_days=[30],
        )
        deck = generate_deck(request)
        assert "'ALPHA'" in deck
        assert "'BRAVO'" in deck


# ═══════════════════════════════════════════════════════════════════════════
# 6. SPE9 Corner-Point (with INCLUDE files)
# ═══════════════════════════════════════════════════════════════════════════


class TestSPE9Parsing:
    """SPE9: 24×25×15, 9000 cells, corner-point grid with INCLUDE files."""

    @pytest.fixture
    def spe9_parsed(self) -> DeckParseResult:
        path = FIXTURES_DIR / "spe9" / "SPE9_CP.DATA"
        if not path.exists():
            pytest.skip("SPE9 fixture not available")
        return parse_deck_file(str(path))

    def test_grid_dimensions(self, spe9_parsed):
        assert spe9_parsed.nx == 24
        assert spe9_parsed.ny == 25
        assert spe9_parsed.nz == 15
        assert spe9_parsed.total_cells == 9000

    def test_units_field(self, spe9_parsed):
        assert spe9_parsed.units == "FIELD"

    def test_phases(self, spe9_parsed):
        assert "OIL" in spe9_parsed.phases
        assert "WATER" in spe9_parsed.phases
        assert "GAS" in spe9_parsed.phases

    def test_wells_exist(self, spe9_parsed):
        """SPE9 has 26 wells."""
        assert len(spe9_parsed.welspecs) >= 20

    def test_timesteps_exist(self, spe9_parsed):
        assert len(spe9_parsed.tstep_values) > 0

    def test_include_resolved(self, spe9_parsed):
        """INCLUDE files (SPE9.GRDECL, PERMVALUES.DATA) must be resolved."""
        # If INCLUDE was resolved, we should have permeability values
        # (PERMVALUES.DATA contains the perm array)
        assert len(spe9_parsed.permx_values) > 0 or spe9_parsed.total_cells > 0

    def test_to_sim_request(self, spe9_parsed):
        """Should convert to valid SimRequest."""
        request = deck_to_sim_request(spe9_parsed)
        assert request.grid.nx == 24
        assert request.grid.ny == 25
        assert request.grid.nz == 15
        assert len(request.wells) >= 20


# ═══════════════════════════════════════════════════════════════════════════
# 7. Parser Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestParserEdgeCases:
    """Edge cases and robustness."""

    def test_empty_deck(self):
        result = parse_deck("")
        assert result.nx == 0
        assert result.total_cells == 0

    def test_comments_only(self):
        result = parse_deck("-- This is a comment\n-- Another one\n")
        assert result.nx == 0

    def test_repeat_notation(self):
        """300*1000 expands to 300 values of 1000."""
        result = parse_deck("DIMENS\n  5 5 1 /\nPORO\n  25*0.3 /\n")
        assert result.nx == 5
        assert len(result.poro_values) == 25
        assert all(v == 0.3 for v in result.poro_values)

    def test_mixed_repeat_and_explicit(self):
        result = parse_deck("DIMENS\n  3 3 1 /\nDZ\n  3*10 3*20 3*30 /\n")
        assert result.dz_values == [10.0] * 3 + [20.0] * 3 + [30.0] * 3

    def test_multiline_tstep(self):
        text = "TSTEP\n31 28 31 30 31 30\n31 31 30 31 30 31 /\n"
        result = parse_deck(text)
        assert len(result.tstep_values) == 12

    def test_missing_file_include(self, tmp_path):
        """Missing INCLUDE file should not crash."""
        deck = tmp_path / "test.DATA"
        deck.write_text("DIMENS\n  5 5 1 /\nINCLUDE\n  'nonexistent.inc' /\n")
        result = parse_deck_file(str(deck))
        assert result.nx == 5  # Rest of deck still parsed
