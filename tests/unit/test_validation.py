"""Tests for Validation Checkpoint Framework."""

import pytest
from clarissa.agent.pipeline.protocols import StageResult
from clarissa.agent.pipeline.validation import (
    ValidationCheckpoint,
    ValidationResult,
    CheckpointDecision,
    StageThresholds,
    create_checkpoint,
    DEFAULT_STAGE_THRESHOLDS,
)


@pytest.fixture
def checkpoint():
    """Create a validation checkpoint for testing."""
    return ValidationCheckpoint(log_decisions=False)


@pytest.fixture
def strict_checkpoint():
    """Create a strict validation checkpoint."""
    return create_checkpoint(strict=True)


class TestStageThresholds:
    """Tests for StageThresholds configuration."""
    
    def test_default_thresholds(self):
        t = StageThresholds()
        assert t.proceed_threshold == 0.8
        assert t.clarify_threshold == 0.5
        assert t.fail_threshold == 0.2
    
    def test_custom_thresholds(self):
        t = StageThresholds(
            proceed_threshold=0.9,
            clarify_threshold=0.6,
            fail_threshold=0.3
        )
        assert t.proceed_threshold == 0.9
    
    def test_invalid_ordering_raises(self):
        with pytest.raises(ValueError, match="must be ordered"):
            StageThresholds(
                proceed_threshold=0.5,
                clarify_threshold=0.8,  # Higher than proceed!
                fail_threshold=0.2
            )
    
    def test_equal_thresholds_valid(self):
        # Edge case: all equal is technically valid
        t = StageThresholds(
            proceed_threshold=0.5,
            clarify_threshold=0.5,
            fail_threshold=0.5
        )
        assert t.proceed_threshold == 0.5


class TestCheckpointDecisions:
    """Tests for checkpoint decision logic."""
    
    def test_proceed_on_high_confidence(self, checkpoint):
        result = StageResult(
            success=True,
            confidence=0.95,
            data={"intent": "SET_RATE"}
        )
        validation = checkpoint.check(result, "intent_recognition")
        
        assert validation.decision == CheckpointDecision.PROCEED
        assert validation.proceed is True
        assert validation.valid is True
        assert validation.clarification_needed is False
    
    def test_clarify_on_medium_confidence(self, checkpoint):
        result = StageResult(
            success=False,
            confidence=0.6,
            data={"intent": "SET_RATE", "alternatives": []},
            errors=["Low confidence - clarification required"]
        )
        # Override to make it a low-confidence success
        result = StageResult(
            success=True,
            confidence=0.6,
            data={"intent": "SET_RATE", "alternatives": []}
        )
        validation = checkpoint.check(result, "intent_recognition")
        
        assert validation.decision == CheckpointDecision.CLARIFY
        assert validation.proceed is False
        assert validation.clarification_needed is True
        assert validation.clarification_prompt is not None
    
    def test_fail_on_very_low_confidence(self, checkpoint):
        result = StageResult(
            success=False,
            confidence=0.1,
            errors=["Could not recognize intent"]
        )
        validation = checkpoint.check(result, "intent_recognition")
        
        assert validation.decision == CheckpointDecision.FAIL
        assert validation.proceed is False
        assert validation.error_message is not None
    
    def test_rollback_on_errors(self, checkpoint):
        result = StageResult(
            success=False,
            confidence=0.7,
            errors=["Missing required entity: well_name"]
        )
        validation = checkpoint.check(result, "entity_extraction")
        
        assert validation.decision == CheckpointDecision.ROLLBACK
        assert validation.proceed is False
        assert validation.rollback_to == "intent_recognition"
    
    def test_rollback_stage_chain(self, checkpoint):
        """Test that rollback points to previous stage."""
        stages = [
            ("speech_recognition", None),  # First stage, no rollback
            ("intent_recognition", "speech_recognition"),
            ("entity_extraction", "intent_recognition"),
            ("asset_validation", "entity_extraction"),
            ("syntax_generation", "asset_validation"),
            ("deck_validation", "syntax_generation"),
        ]
        
        for stage, expected_rollback in stages:
            result = StageResult(
                success=False,
                confidence=0.5,
                errors=["Test error"]
            )
            validation = checkpoint.check(result, stage)
            assert validation.rollback_to == expected_rollback, \
                f"Stage {stage} should rollback to {expected_rollback}"


class TestClarificationPrompts:
    """Tests for clarification prompt generation."""
    
    def test_intent_clarification_with_alternatives(self, checkpoint):
        result = StageResult(
            success=True,
            confidence=0.6,
            data={
                "intent": "SET_RATE",
                "alternatives": [
                    {"intent": "SET_PRESSURE", "confidence": 0.4},
                    {"intent": "GET_PRODUCTION", "confidence": 0.3},
                ]
            }
        )
        validation = checkpoint.check(result, "intent_recognition")
        
        assert "SET_PRESSURE" in validation.clarification_prompt
        assert "40%" in validation.clarification_prompt
    
    def test_entity_clarification_with_missing(self, checkpoint):
        result = StageResult(
            success=True,
            confidence=0.6,
            data={
                "entities": {"rate_value": 500},
                "missing": ["well_name", "rate_unit"]
            }
        )
        validation = checkpoint.check(result, "entity_extraction")
        
        assert "well_name" in validation.clarification_prompt
        assert "rate_unit" in validation.clarification_prompt


class TestStageSpecificThresholds:
    """Tests for stage-specific threshold configuration."""
    
    def test_deck_validation_stricter(self):
        """Deck validation should have higher thresholds."""
        checkpoint = ValidationCheckpoint(log_decisions=False)
        
        # Same confidence should pass intent but fail deck validation
        result = StageResult(success=True, confidence=0.85, data={})
        
        intent_val = checkpoint.check(result, "intent_recognition")
        deck_val = checkpoint.check(result, "deck_validation")
        
        assert intent_val.decision == CheckpointDecision.PROCEED
        assert deck_val.decision == CheckpointDecision.CLARIFY
    
    def test_custom_thresholds_override(self):
        custom = {
            "intent_recognition": StageThresholds(0.5, 0.3, 0.1)
        }
        checkpoint = ValidationCheckpoint(thresholds=custom, log_decisions=False)
        
        result = StageResult(success=True, confidence=0.55, data={})
        validation = checkpoint.check(result, "intent_recognition")
        
        assert validation.decision == CheckpointDecision.PROCEED


class TestCheckpointHistory:
    """Tests for decision history tracking."""
    
    def test_history_recorded(self, checkpoint):
        results = [
            StageResult(success=True, confidence=0.9, data={}),
            StageResult(success=True, confidence=0.6, data={}),
            StageResult(success=False, confidence=0.1, errors=["fail"]),
        ]
        
        for result in results:
            checkpoint.check(result, "intent_recognition")
        
        history = checkpoint.get_history()
        assert len(history) == 3
    
    def test_clear_history(self, checkpoint):
        checkpoint.check(
            StageResult(success=True, confidence=0.9, data={}),
            "intent_recognition"
        )
        assert len(checkpoint.get_history()) == 1
        
        checkpoint.clear_history()
        assert len(checkpoint.get_history()) == 0
    
    def test_summary(self, checkpoint):
        # Add various decisions
        checkpoint.check(
            StageResult(success=True, confidence=0.95, data={}),
            "intent_recognition"
        )
        checkpoint.check(
            StageResult(success=True, confidence=0.6, data={}),
            "entity_extraction"
        )
        checkpoint.check(
            StageResult(success=False, confidence=0.1, errors=["fail"]),
            "syntax_generation"
        )
        
        summary = checkpoint.summary()
        assert summary["total"] == 3
        assert summary["proceed"] == 1
        assert summary["clarify"] == 1
        assert summary["fail"] == 1


class TestCreateCheckpoint:
    """Tests for factory function."""
    
    def test_default_checkpoint(self):
        checkpoint = create_checkpoint()
        assert isinstance(checkpoint, ValidationCheckpoint)
    
    def test_strict_checkpoint(self):
        checkpoint = create_checkpoint(strict=True)
        thresholds = checkpoint.default_thresholds
        
        assert thresholds.proceed_threshold == 0.9
        assert thresholds.clarify_threshold == 0.7
    
    def test_custom_thresholds_via_factory(self):
        custom = {
            "my_stage": StageThresholds(0.95, 0.8, 0.5)
        }
        checkpoint = create_checkpoint(custom_thresholds=custom)
        
        assert "my_stage" in checkpoint.thresholds


class TestValidationResultDataclass:
    """Tests for ValidationResult dataclass."""
    
    def test_timestamp_auto_set(self):
        result = ValidationResult(
            decision=CheckpointDecision.PROCEED,
            valid=True,
            confidence=0.9,
            proceed=True,
            stage="test"
        )
        assert result.timestamp is not None
    
    def test_metadata_default_empty(self):
        result = ValidationResult(
            decision=CheckpointDecision.PROCEED,
            valid=True,
            confidence=0.9,
            proceed=True,
            stage="test"
        )
        assert result.metadata == {}


# Integration-style tests
class TestPipelineIntegration:
    """Tests simulating full pipeline validation."""
    
    def test_successful_pipeline_flow(self, checkpoint):
        """Simulate a successful pipeline run."""
        # Intent recognition - high confidence
        intent_result = StageResult(
            success=True,
            confidence=0.92,
            data={"intent": "SET_RATE", "category": "well_operations"}
        )
        intent_val = checkpoint.check(intent_result, "intent_recognition")
        assert intent_val.proceed
        
        # Entity extraction - high confidence
        entity_result = StageResult(
            success=True,
            confidence=0.88,
            data={"entities": {"well_name": "PROD-01", "rate_value": 500}}
        )
        entity_val = checkpoint.check(entity_result, "entity_extraction")
        assert entity_val.proceed
        
        # Summary should show all passed
        summary = checkpoint.summary()
        assert summary["proceed"] == 2
        assert summary["success_rate"] == 1.0
    
    def test_pipeline_with_clarification(self, checkpoint):
        """Simulate pipeline that needs clarification."""
        # Intent recognition - medium confidence
        intent_result = StageResult(
            success=True,
            confidence=0.65,
            data={
                "intent": "SET_RATE",
                "alternatives": [{"intent": "SET_PRESSURE", "confidence": 0.5}]
            }
        )
        intent_val = checkpoint.check(intent_result, "intent_recognition")
        
        assert not intent_val.proceed
        assert intent_val.clarification_needed
        # Pipeline should stop here and ask for clarification