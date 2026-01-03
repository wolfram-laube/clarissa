"""Tests for Intent Recognition Stage.

Tests the RuleBasedRecognizer with various input patterns.
"""

import pytest
from clarissa.agent.pipeline.intent import (
    RuleBasedRecognizer,
    HybridRecognizer,
    create_recognizer,
)
from clarissa.agent.pipeline.protocols import StageResult


@pytest.fixture
def recognizer():
    """Create a rule-based recognizer for testing."""
    return RuleBasedRecognizer(confidence_threshold=0.7)


class TestRuleBasedRecognizer:
    """Tests for RuleBasedRecognizer."""
    
    # Simulation Control
    def test_run_simulation(self, recognizer):
        result = recognizer.recognize("Run the simulation")
        assert result.success
        assert result.data["intent"] == "RUN_SIMULATION"
        assert result.confidence >= 0.7
    
    def test_run_simulation_alternate(self, recognizer):
        result = recognizer.recognize("Start the model")
        assert result.data["intent"] == "RUN_SIMULATION"
    
    def test_stop_simulation(self, recognizer):
        result = recognizer.recognize("Stop the simulation")
        assert result.data["intent"] == "STOP_SIMULATION"
    
    def test_restart_simulation(self, recognizer):
        result = recognizer.recognize("Restart from January checkpoint")
        assert result.data["intent"] == "RESTART_SIMULATION"
    
    # Well Operations
    def test_add_well(self, recognizer):
        result = recognizer.recognize("Add a new producer called PROD-01")
        assert result.data["intent"] == "ADD_WELL"
        assert result.data["category"] == "well_operations"
    
    def test_shut_well(self, recognizer):
        result = recognizer.recognize("Shut well PROD-01")
        assert result.data["intent"] == "SHUT_WELL"
    
    def test_open_well(self, recognizer):
        result = recognizer.recognize("Open well INJ-A")
        assert result.data["intent"] == "OPEN_WELL"
    
    def test_set_rate(self, recognizer):
        result = recognizer.recognize("Set well P1 rate to 500 bbl/day")
        assert result.data["intent"] == "SET_RATE"
        assert result.confidence >= 0.7
    
    def test_set_rate_with_phase(self, recognizer):
        result = recognizer.recognize("Set oil rate to 1000 STB/day")
        assert result.data["intent"] == "SET_RATE"
    
    def test_set_pressure(self, recognizer):
        result = recognizer.recognize("Set BHP to 2000 psi")
        assert result.data["intent"] == "SET_PRESSURE"
    
    def test_set_pressure_bottomhole(self, recognizer):
        result = recognizer.recognize("Change bottomhole pressure to 1500 psia")
        assert result.data["intent"] == "SET_PRESSURE"
    
    # Schedule Operations
    def test_set_date(self, recognizer):
        result = recognizer.recognize("Advance to 2026-06-01")
        assert result.data["intent"] == "SET_DATE"
    
    def test_set_date_month(self, recognizer):
        result = recognizer.recognize("Move forward to January 2026")
        assert result.data["intent"] == "SET_DATE"
    
    def test_add_timestep(self, recognizer):
        result = recognizer.recognize("Add 30 day timestep")
        assert result.data["intent"] == "ADD_TIMESTEP"
    
    # Query Operations
    def test_get_production(self, recognizer):
        result = recognizer.recognize("Show oil production for PROD-01")
        assert result.data["intent"] == "GET_PRODUCTION"
        assert result.data["category"] == "query_operations"
    
    def test_get_pressure(self, recognizer):
        result = recognizer.recognize("What's the current reservoir pressure?")
        assert result.data["intent"] == "GET_PRESSURE"
    
    def test_compare_scenarios(self, recognizer):
        result = recognizer.recognize("Compare BASE vs HIGH scenario")
        assert result.data["intent"] == "COMPARE_SCENARIOS"
    
    def test_get_summary(self, recognizer):
        result = recognizer.recognize("Show simulation summary")
        assert result.data["intent"] == "GET_SUMMARY"
    
    # Validation
    def test_validate_deck(self, recognizer):
        result = recognizer.recognize("Validate the deck for syntax errors")
        assert result.data["intent"] == "VALIDATE_DECK"
    
    def test_check_physics(self, recognizer):
        result = recognizer.recognize("Check material balance")
        assert result.data["intent"] == "CHECK_PHYSICS"
    
    # Help
    def test_get_help(self, recognizer):
        result = recognizer.recognize("Help with WCONPROD keyword")
        assert result.data["intent"] == "GET_HELP"
    
    def test_explain_error(self, recognizer):
        result = recognizer.recognize("What does error 123 mean?")
        assert result.data["intent"] == "EXPLAIN_ERROR"
    
    # Edge Cases
    def test_empty_input(self, recognizer):
        result = recognizer.recognize("")
        assert not result.success
        assert "Empty input" in result.errors[0]
    
    def test_whitespace_only(self, recognizer):
        result = recognizer.recognize("   ")
        assert not result.success
    
    def test_ambiguous_input(self, recognizer):
        result = recognizer.recognize("do something")
        # Should return low confidence or failure
        assert result.confidence < 0.7 or not result.success
    
    def test_gibberish(self, recognizer):
        result = recognizer.recognize("asdfghjkl qwerty")
        # Should not match any intent
        assert not result.success or result.confidence == 0.0
    
    def test_alternatives_returned(self, recognizer):
        # Query that might match multiple intents
        result = recognizer.recognize("Show pressure and production data")
        # Should have alternatives
        if result.success or result.data:
            assert "alternatives" in result.data


class TestStageResultInvariants:
    """Test StageResult validation invariants."""
    
    def test_success_with_errors_raises(self):
        with pytest.raises(ValueError, match="Successful result cannot have errors"):
            StageResult(success=True, confidence=0.9, errors=["oops"])
    
    def test_failure_without_errors_raises(self):
        with pytest.raises(ValueError, match="Failed result must have at least one error"):
            StageResult(success=False, confidence=0.5, errors=[])
    
    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Confidence must be in"):
            StageResult(success=True, confidence=1.5)
        
        with pytest.raises(ValueError, match="Confidence must be in"):
            StageResult(success=False, confidence=-0.1, errors=["error"])
    
    def test_failure_factory(self):
        result = StageResult.failure(["Error 1", "Error 2"], confidence=0.3)
        assert not result.success
        assert result.confidence == 0.3
        assert len(result.errors) == 2
    
    def test_low_confidence_factory(self):
        result = StageResult.low_confidence({"intent": "TEST"}, confidence=0.5)
        assert not result.success
        assert result.confidence == 0.5
        assert result.data["intent"] == "TEST"


class TestHybridRecognizer:
    """Tests for HybridRecognizer."""
    
    def test_uses_rules_for_clear_input(self):
        recognizer = HybridRecognizer()
        result = recognizer.recognize("Run the simulation")
        assert result.success
        assert result.metadata.get("recognizer") == "rule_based"
    
    def test_returns_result_for_ambiguous_input(self):
        recognizer = HybridRecognizer()
        result = recognizer.recognize("maybe do something with the well")
        # Should still return something (even if low confidence)
        # because LLM is not implemented yet
        assert result is not None


class TestCreateRecognizer:
    """Tests for factory function."""
    
    def test_create_rules(self):
        recognizer = create_recognizer("rules")
        assert isinstance(recognizer, RuleBasedRecognizer)
    
    def test_create_hybrid(self):
        recognizer = create_recognizer("hybrid")
        assert isinstance(recognizer, HybridRecognizer)
    
    def test_create_invalid_mode(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            create_recognizer("invalid")
    
    def test_create_with_kwargs(self):
        recognizer = create_recognizer("rules", confidence_threshold=0.5)
        assert recognizer.confidence_threshold == 0.5


# Parameterized tests for comprehensive coverage
@pytest.mark.parametrize("text,expected_intent", [
    ("Run the simulation", "RUN_SIMULATION"),
    ("Execute CASE1", "RUN_SIMULATION"),
    ("Start the model", "RUN_SIMULATION"),
    ("Stop the run", "STOP_SIMULATION"),
    ("Halt simulation", "STOP_SIMULATION"),
    ("Add producer WELL-1", "ADD_WELL"),
    ("Create new injector", "ADD_WELL"),
    ("Shut PROD-01", "SHUT_WELL"),
    ("Close well INJ-A", "SHUT_WELL"),
    ("Set rate to 500 bbl/day", "SET_RATE"),
    ("Change oil rate to 1000 STB/day", "SET_RATE"),
    ("Set BHP to 2000 psi", "SET_PRESSURE"),
    ("Show production", "GET_PRODUCTION"),
    ("What is the pressure?", "GET_PRESSURE"),
    ("Validate deck", "VALIDATE_DECK"),
    ("Help with WCONPROD", "GET_HELP"),
])
def test_intent_recognition_parametrized(text, expected_intent):
    """Parametrized test for various intent patterns."""
    recognizer = RuleBasedRecognizer(confidence_threshold=0.5)
    result = recognizer.recognize(text)
    assert result.data is not None, f"No match for: {text}"
    assert result.data["intent"] == expected_intent, \
        f"Expected {expected_intent} for '{text}', got {result.data['intent']}"