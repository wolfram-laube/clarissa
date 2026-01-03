"""Validation Checkpoint Framework.

Implements the validation checkpoint pattern between NLP pipeline stages
per ADR-009. Each checkpoint enforces the three-state decision:

1. High confidence, valid → Proceed to next stage
2. Low confidence → Request clarification, do not proceed  
3. Invalid → Roll back, explain failure

Usage:
    from clarissa.agent.pipeline.validation import ValidationCheckpoint
    
    checkpoint = ValidationCheckpoint(threshold=0.8)
    result = intent_recognizer.recognize(text)
    validation = checkpoint.check(result, stage="intent_recognition")
    
    if validation.proceed:
        # Continue to next stage
        pass
    elif validation.clarification_needed:
        # Ask user for clarification
        print(validation.clarification_prompt)
    else:
        # Handle failure
        print(validation.error_message)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from clarissa.agent.pipeline.protocols import StageResult


# Configure logging
logger = logging.getLogger("clarissa.pipeline.validation")


class CheckpointDecision(Enum):
    """Possible decisions at a validation checkpoint."""
    PROCEED = "proceed"
    CLARIFY = "clarify"
    ROLLBACK = "rollback"
    FAIL = "fail"


@dataclass
class ValidationResult:
    """Result of a validation checkpoint check.
    
    Attributes:
        decision: The checkpoint decision (proceed, clarify, rollback, fail).
        valid: Whether the stage result is valid.
        confidence: Confidence score from the stage.
        proceed: Whether to proceed to next stage.
        stage: Name of the stage that was validated.
        clarification_needed: Whether clarification is required.
        clarification_prompt: Suggested prompt to ask user.
        rollback_to: Stage to rollback to on failure.
        error_message: Human-readable error description.
        metadata: Additional validation metadata.
    """
    decision: CheckpointDecision
    valid: bool
    confidence: float
    proceed: bool
    stage: str
    clarification_needed: bool = False
    clarification_prompt: str | None = None
    rollback_to: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StageThresholds:
    """Confidence thresholds for a specific stage.
    
    Attributes:
        proceed_threshold: Minimum confidence to proceed (default 0.8).
        clarify_threshold: Below this, request clarification (default 0.5).
        fail_threshold: Below this, fail immediately (default 0.2).
    """
    proceed_threshold: float = 0.8
    clarify_threshold: float = 0.5
    fail_threshold: float = 0.2
    
    def __post_init__(self):
        """Validate threshold ordering."""
        if not (self.fail_threshold <= self.clarify_threshold <= self.proceed_threshold):
            raise ValueError(
                f"Thresholds must be ordered: fail ({self.fail_threshold}) "
                f"<= clarify ({self.clarify_threshold}) "
                f"<= proceed ({self.proceed_threshold})"
            )


# Default thresholds per stage (can be customized)
DEFAULT_STAGE_THRESHOLDS: dict[str, StageThresholds] = {
    "speech_recognition": StageThresholds(0.85, 0.6, 0.3),
    "intent_recognition": StageThresholds(0.8, 0.5, 0.2),
    "entity_extraction": StageThresholds(0.75, 0.45, 0.2),
    "asset_validation": StageThresholds(0.9, 0.7, 0.4),
    "syntax_generation": StageThresholds(0.85, 0.6, 0.3),
    "deck_validation": StageThresholds(0.95, 0.8, 0.5),
}


# Clarification prompt templates
CLARIFICATION_TEMPLATES: dict[str, str] = {
    "intent_recognition": (
        "I'm not sure I understood your request. Did you mean to:\n"
        "{alternatives}\n"
        "Or could you rephrase what you'd like to do?"
    ),
    "entity_extraction": (
        "I found some information but I'm missing a few details:\n"
        "- Missing: {missing}\n"
        "Could you provide more specific information?"
    ),
    "asset_validation": (
        "I couldn't verify some references:\n"
        "{unverified}\n"
        "Please check the names and try again."
    ),
    "default": (
        "I need more information to proceed. "
        "Could you provide more details about your request?"
    ),
}


class ValidationCheckpoint:
    """Validation checkpoint for pipeline stages.
    
    Enforces the three-state decision pattern:
    1. Proceed - confidence >= proceed_threshold, no errors
    2. Clarify - confidence between clarify and proceed thresholds
    3. Rollback/Fail - confidence < clarify_threshold or errors present
    
    Attributes:
        thresholds: Dict mapping stage names to their thresholds.
        default_thresholds: Thresholds for unknown stages.
        log_decisions: Whether to log checkpoint decisions.
    """
    
    def __init__(
        self,
        thresholds: dict[str, StageThresholds] | None = None,
        default_thresholds: StageThresholds | None = None,
        log_decisions: bool = True
    ):
        """Initialize checkpoint with thresholds.
        
        Args:
            thresholds: Stage-specific thresholds.
            default_thresholds: Fallback thresholds for unknown stages.
            log_decisions: Whether to log decisions.
        """
        self.thresholds = {**DEFAULT_STAGE_THRESHOLDS, **(thresholds or {})}
        self.default_thresholds = default_thresholds or StageThresholds()
        self.log_decisions = log_decisions
        self._decision_history: list[ValidationResult] = []
    
    def get_thresholds(self, stage: str) -> StageThresholds:
        """Get thresholds for a stage."""
        return self.thresholds.get(stage, self.default_thresholds)
    
    def _generate_clarification_prompt(
        self, 
        stage: str, 
        result: StageResult
    ) -> str:
        """Generate a clarification prompt based on stage and result."""
        template = CLARIFICATION_TEMPLATES.get(
            stage, 
            CLARIFICATION_TEMPLATES["default"]
        )
        
        # Format template based on result data
        format_args = {}
        
        if result.data:
            # Intent alternatives
            if "alternatives" in result.data:
                alts = result.data["alternatives"]
                if alts:
                    format_args["alternatives"] = "\n".join(
                        f"  - {a['intent']} ({a['confidence']:.0%})" 
                        for a in alts[:3]
                    )
                else:
                    format_args["alternatives"] = "  (no clear alternatives)"
            
            # Missing entities
            if "missing" in result.data:
                format_args["missing"] = ", ".join(result.data["missing"])
            
            # Unverified references
            if "unverified" in result.data:
                format_args["unverified"] = ", ".join(result.data["unverified"])
        
        try:
            return template.format(**format_args)
        except KeyError:
            return CLARIFICATION_TEMPLATES["default"]
    
    def _get_rollback_stage(self, stage: str) -> str | None:
        """Determine which stage to rollback to."""
        stage_order = [
            "speech_recognition",
            "intent_recognition", 
            "entity_extraction",
            "asset_validation",
            "syntax_generation",
            "deck_validation",
        ]
        
        try:
            idx = stage_order.index(stage)
            if idx > 0:
                return stage_order[idx - 1]
        except ValueError:
            pass
        
        return None
    
    def check(self, result: StageResult, stage: str) -> ValidationResult:
        """Check a stage result against validation thresholds.
        
        Args:
            result: The StageResult from a pipeline stage.
            stage: Name of the stage (e.g., "intent_recognition").
        
        Returns:
            ValidationResult with decision and metadata.
        """
        thresholds = self.get_thresholds(stage)
        
        # Determine decision based on confidence and errors
        if result.success and result.confidence >= thresholds.proceed_threshold:
            # Case 1: High confidence, valid → Proceed
            decision = CheckpointDecision.PROCEED
            validation = ValidationResult(
                decision=decision,
                valid=True,
                confidence=result.confidence,
                proceed=True,
                stage=stage,
                metadata={"threshold_used": thresholds.proceed_threshold}
            )
        
        elif result.confidence < thresholds.fail_threshold:
            # Case 3: Very low confidence → Fail
            decision = CheckpointDecision.FAIL
            validation = ValidationResult(
                decision=decision,
                valid=False,
                confidence=result.confidence,
                proceed=False,
                stage=stage,
                error_message=f"Confidence too low ({result.confidence:.0%}). "
                             f"Unable to proceed with {stage}.",
                rollback_to=self._get_rollback_stage(stage),
                metadata={"threshold_used": thresholds.fail_threshold}
            )
        
        elif not result.success and result.errors:
            # Case 3: Errors present → Rollback
            decision = CheckpointDecision.ROLLBACK
            validation = ValidationResult(
                decision=decision,
                valid=False,
                confidence=result.confidence,
                proceed=False,
                stage=stage,
                error_message="; ".join(result.errors),
                rollback_to=self._get_rollback_stage(stage),
                metadata={"errors": result.errors}
            )
        
        elif result.confidence < thresholds.proceed_threshold:
            # Case 2: Low confidence → Request clarification
            decision = CheckpointDecision.CLARIFY
            validation = ValidationResult(
                decision=decision,
                valid=True,  # Result is valid but uncertain
                confidence=result.confidence,
                proceed=False,
                stage=stage,
                clarification_needed=True,
                clarification_prompt=self._generate_clarification_prompt(stage, result),
                metadata={"threshold_used": thresholds.proceed_threshold}
            )
        
        else:
            # Default: Proceed (shouldn't normally reach here)
            decision = CheckpointDecision.PROCEED
            validation = ValidationResult(
                decision=decision,
                valid=True,
                confidence=result.confidence,
                proceed=True,
                stage=stage,
            )
        
        # Log the decision
        if self.log_decisions:
            self._log_decision(validation, result)
        
        # Store in history
        self._decision_history.append(validation)
        
        return validation
    
    def _log_decision(self, validation: ValidationResult, result: StageResult) -> None:
        """Log a checkpoint decision."""
        log_data = {
            "stage": validation.stage,
            "decision": validation.decision.value,
            "confidence": f"{validation.confidence:.2%}",
            "proceed": validation.proceed,
        }
        
        if validation.decision == CheckpointDecision.PROCEED:
            logger.info(f"✓ Checkpoint PASSED: {validation.stage} ({validation.confidence:.0%})")
        elif validation.decision == CheckpointDecision.CLARIFY:
            logger.warning(f"? Checkpoint CLARIFY: {validation.stage} ({validation.confidence:.0%})")
        elif validation.decision == CheckpointDecision.ROLLBACK:
            logger.error(f"✗ Checkpoint ROLLBACK: {validation.stage} → {validation.rollback_to}")
        else:
            logger.error(f"✗ Checkpoint FAIL: {validation.stage} ({validation.confidence:.0%})")
    
    def get_history(self) -> list[ValidationResult]:
        """Get history of validation decisions."""
        return self._decision_history.copy()
    
    def clear_history(self) -> None:
        """Clear decision history."""
        self._decision_history.clear()
    
    def summary(self) -> dict[str, Any]:
        """Get summary of validation decisions."""
        if not self._decision_history:
            return {"total": 0}
        
        decisions = [v.decision for v in self._decision_history]
        return {
            "total": len(decisions),
            "proceed": decisions.count(CheckpointDecision.PROCEED),
            "clarify": decisions.count(CheckpointDecision.CLARIFY),
            "rollback": decisions.count(CheckpointDecision.ROLLBACK),
            "fail": decisions.count(CheckpointDecision.FAIL),
            "success_rate": decisions.count(CheckpointDecision.PROCEED) / len(decisions),
        }


# Convenience factory
def create_checkpoint(
    strict: bool = False,
    custom_thresholds: dict[str, StageThresholds] | None = None
) -> ValidationCheckpoint:
    """Factory function to create validation checkpoints.
    
    Args:
        strict: If True, use higher thresholds.
        custom_thresholds: Optional custom thresholds.
    
    Returns:
        Configured ValidationCheckpoint.
    """
    if strict:
        default = StageThresholds(
            proceed_threshold=0.9,
            clarify_threshold=0.7,
            fail_threshold=0.4
        )
    else:
        default = StageThresholds()
    
    return ValidationCheckpoint(
        thresholds=custom_thresholds,
        default_thresholds=default
    )


__all__ = [
    "ValidationCheckpoint",
    "ValidationResult",
    "CheckpointDecision",
    "StageThresholds",
    "create_checkpoint",
    "DEFAULT_STAGE_THRESHOLDS",
]