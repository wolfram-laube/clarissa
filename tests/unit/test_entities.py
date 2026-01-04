"""Tests for Entity Extraction Stage.

Tests the RuleBasedEntityExtractor with various input patterns.
"""

import pytest
from clarissa.agent.pipeline.entities import (
    EntityExtractor,
    RuleBasedEntityExtractor,
    RateValue,
    PressureValue,
)


@pytest.fixture
def extractor():
    """Create an entity extractor for testing."""
    return RuleBasedEntityExtractor(confidence_threshold=0.7)


class TestRateValue:
    """Tests for rate value handling."""
    
    def test_standard_conversion(self):
        rate = RateValue(value=100, unit="M3/DAY")
        std = rate.to_standard()
        assert std.unit == "STB/DAY"
        assert abs(std.value - 628.98) < 1  # ~6.29 bbl per m³
    
    def test_mscf_unchanged(self):
        rate = RateValue(value=5000, unit="MSCF/DAY")
        std = rate.to_standard()
        assert std.unit == "MSCF/DAY"
        assert std.value == 5000
    
    def test_mmscf_to_mscf(self):
        rate = RateValue(value=5, unit="MMSCF/DAY")
        std = rate.to_standard()
        assert std.unit == "MSCF/DAY"
        assert std.value == 5000


class TestPressureValue:
    """Tests for pressure value handling."""
    
    def test_bar_to_psi(self):
        pressure = PressureValue(value=100, unit="BAR")
        std = pressure.to_standard()
        assert std.unit == "PSIA"
        assert abs(std.value - 1450.38) < 1
    
    def test_kpa_to_psi(self):
        pressure = PressureValue(value=1000, unit="KPA")
        std = pressure.to_standard()
        assert std.unit == "PSIA"
        assert abs(std.value - 145.038) < 1


class TestWellNameExtraction:
    """Tests for well name extraction."""
    
    def test_simple_well_name(self, extractor):
        result = extractor.extract("Set rate for PROD-01", "SET_RATE")
        assert "well_name" in result.data["entities"]
        assert result.data["entities"]["well_name"] == "PROD-01"
    
    def test_well_with_underscore(self, extractor):
        result = extractor.extract("Shut well INJ_A", "SHUT_WELL")
        assert result.data["entities"]["well_name"] == "INJ_A"
    
    def test_short_well_name(self, extractor):
        result = extractor.extract("Open P1", "OPEN_WELL")
        assert result.data["entities"]["well_name"] == "P1"
    
    def test_multiple_wells_returns_first(self, extractor):
        result = extractor.extract("Compare PROD-01 and PROD-02", "GET_PRODUCTION")
        # Should return at least one well
        assert "well_name" in result.data["entities"]


class TestRateExtraction:
    """Tests for rate value extraction."""
    
    def test_bbl_per_day(self, extractor):
        result = extractor.extract("Set rate to 500 bbl/day", "SET_RATE")
        assert result.data["entities"]["rate_value"] == 500.0
        assert "BBL" in result.data["entities"]["rate_unit"]
    
    def test_stb_per_day(self, extractor):
        result = extractor.extract("Oil rate 1000 STB/day", "SET_RATE")
        assert result.data["entities"]["rate_value"] == 1000.0
    
    def test_mscf_per_day(self, extractor):
        result = extractor.extract("Gas rate 5000 mscf/day", "SET_RATE")
        assert result.data["entities"]["rate_value"] == 5000.0
    
    def test_decimal_rate(self, extractor):
        result = extractor.extract("Set rate to 123.5 bbl/day", "SET_RATE")
        assert result.data["entities"]["rate_value"] == 123.5
    
    def test_rate_with_per(self, extractor):
        result = extractor.extract("500 barrels per day", "SET_RATE")
        assert result.data["entities"]["rate_value"] == 500.0


class TestPressureExtraction:
    """Tests for pressure value extraction."""
    
    def test_psi(self, extractor):
        result = extractor.extract("Set BHP to 2000 psi", "SET_PRESSURE")
        assert result.data["entities"]["pressure_value"] == 2000.0
        assert result.data["entities"]["pressure_unit"] == "PSI"
    
    def test_psia(self, extractor):
        result = extractor.extract("Pressure 1500 psia", "SET_PRESSURE")
        assert result.data["entities"]["pressure_value"] == 1500.0
        assert result.data["entities"]["pressure_unit"] == "PSIA"
    
    def test_bar(self, extractor):
        result = extractor.extract("200 bar pressure", "SET_PRESSURE")
        assert result.data["entities"]["pressure_value"] == 200.0
        assert result.data["entities"]["pressure_unit"] == "BAR"
    
    def test_bhp_type_detection(self, extractor):
        result = extractor.extract("Set bottomhole pressure to 2000 psi", "SET_PRESSURE")
        assert result.data["entities"].get("pressure_type") == "BHP"
    
    def test_thp_type_detection(self, extractor):
        result = extractor.extract("Set THP to 500 psi", "SET_PRESSURE")
        assert result.data["entities"].get("pressure_type") == "THP"


class TestDateExtraction:
    """Tests for date extraction."""
    
    def test_iso_date(self, extractor):
        result = extractor.extract("Set date to 2025-06-15", "SET_DATE")
        assert result.data["entities"]["target_date"] == "2025-06-15"
    
    def test_month_year(self, extractor):
        result = extractor.extract("Advance to January 2026", "SET_DATE")
        assert result.data["entities"]["target_date"] == "2026-01-01"
    
    def test_month_day(self, extractor):
        result = extractor.extract("Start on March 15th", "SET_DATE")
        assert "03-15" in result.data["entities"]["target_date"]


class TestDurationExtraction:
    """Tests for duration/timestep extraction."""
    
    def test_days(self, extractor):
        result = extractor.extract("Add 30 day timestep", "ADD_TIMESTEP")
        assert result.data["entities"]["timestep_size"] == 30
        assert result.data["entities"]["timestep_unit"] == "DAY"
    
    def test_months(self, extractor):
        result = extractor.extract("6 months forward", "ADD_TIMESTEP")
        assert result.data["entities"]["timestep_size"] == 6
        assert result.data["entities"]["timestep_unit"] == "MONTH"


class TestFluidExtraction:
    """Tests for fluid/phase extraction."""
    
    def test_oil(self, extractor):
        result = extractor.extract("Show oil production", "GET_PRODUCTION")
        assert result.data["entities"]["phase"] == "OIL"
    
    def test_water(self, extractor):
        result = extractor.extract("Water injection rate", "GET_PRODUCTION")
        assert result.data["entities"]["phase"] == "WATER"
    
    def test_gas(self, extractor):
        result = extractor.extract("Gas rate", "GET_PRODUCTION")
        assert result.data["entities"]["phase"] == "GAS"


class TestWellTypeExtraction:
    """Tests for well type extraction."""
    
    def test_producer(self, extractor):
        result = extractor.extract("Add producer", "ADD_WELL")
        assert result.data["entities"]["well_type"] == "PRODUCER"
    
    def test_injector(self, extractor):
        result = extractor.extract("New injector well", "ADD_WELL")
        assert result.data["entities"]["well_type"] == "INJECTOR"
    
    def test_abbreviation_prod(self, extractor):
        result = extractor.extract("Prod well P1", "ADD_WELL")
        assert result.data["entities"]["well_type"] == "PRODUCER"


class TestGridLocationExtraction:
    """Tests for grid I,J location extraction."""
    
    def test_i_j_format(self, extractor):
        result = extractor.extract("Well at I=10 J=15", "ADD_WELL")
        assert result.data["entities"]["location_i"] == 10
        assert result.data["entities"]["location_j"] == 15
    
    def test_i_j_colon(self, extractor):
        result = extractor.extract("Location I:5 J:8", "ADD_WELL")
        assert result.data["entities"]["location_i"] == 5
        assert result.data["entities"]["location_j"] == 8


class TestMissingEntities:
    """Tests for required entity validation."""
    
    def test_missing_required_fails(self, extractor):
        # SET_RATE requires well_name, rate_value, rate_type
        result = extractor.extract("Set rate", "SET_RATE")
        assert not result.success
        assert "missing" in result.data
        assert len(result.data["missing"]) > 0
    
    def test_partial_extraction(self, extractor):
        # Has rate but no well
        result = extractor.extract("Set rate to 500 bbl/day", "SET_RATE")
        # Should have some entities but might be missing well_name
        assert "rate_value" in result.data["entities"]


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_input(self, extractor):
        result = extractor.extract("", "SET_RATE")
        assert not result.success
        assert "Empty input" in result.errors[0]
    
    def test_unknown_intent(self, extractor):
        result = extractor.extract("Some text", "UNKNOWN_INTENT")
        assert not result.success
        assert "Unknown intent" in result.errors[0]
    
    def test_no_entities(self, extractor):
        result = extractor.extract("do something", "GET_SUMMARY")
        # GET_SUMMARY has no required entities, should succeed
        assert result.success or result.confidence > 0


# Parametrized comprehensive tests
@pytest.mark.parametrize("text,intent,expected_entity,expected_value", [
    ("Set PROD-01 rate to 500 bbl/day", "SET_RATE", "well_name", "PROD-01"),
    ("Set PROD-01 rate to 500 bbl/day", "SET_RATE", "rate_value", 500.0),
    ("Shut well INJ-A", "SHUT_WELL", "well_name", "INJ-A"),
    ("BHP 2000 psi", "SET_PRESSURE", "pressure_value", 2000.0),
    ("Date 2025-12-01", "SET_DATE", "target_date", "2025-12-01"),
    ("30 day timestep", "ADD_TIMESTEP", "timestep_size", 30),
    ("oil production", "GET_PRODUCTION", "phase", "OIL"),
    ("add producer", "ADD_WELL", "well_type", "PRODUCER"),
])
def test_entity_extraction_parametrized(extractor, text, intent, expected_entity, expected_value):
    """Parametrized test for entity extraction."""
    result = extractor.extract(text, intent)
    assert result.data is not None
    assert expected_entity in result.data["entities"], \
        f"Expected {expected_entity} in entities for '{text}'"
    assert result.data["entities"][expected_entity] == expected_value, \
        f"Expected {expected_value} for {expected_entity}, got {result.data['entities'][expected_entity]}"



# =============================================================================
# Group Name Entity Tests (IRENA recommendation)
# =============================================================================

class TestGroupNameExtraction:
    """Tests for group_name entity extraction."""

    @pytest.fixture
    def extractor(self):
        return RuleBasedEntityExtractor()

    @pytest.mark.parametrize("text,expected_group", [
        ("add group FIELD_NORTH", "FIELD_NORTH"),
        ("set group G1 rate", "G1"),
    ])
    def test_explicit_group_names(self, extractor, text, expected_group):
        result = extractor.extract(text, intent="SET_GROUP_RATE")
        entities = result.data["entities"]
        groups = [e for e in entities if e.name == "group_name"]
        assert len(groups) >= 1
        assert any(g.value == expected_group for g in groups)