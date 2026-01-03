"""NLP Pipeline Stage Protocols.

Defines the interfaces (Protocols) for each stage of CLARISSA's multi-stage
NLP translation pipeline per ADR-009.

Each stage follows the same validation pattern:
1. High confidence, valid: Proceed to next stage
2. Low confidence: Request clarification; do not proceed
3. Invalid: Roll back; explain failure

Usage:
    from clarissa.agent.pipeline.protocols import IntentRecognizer, StageResult
    
    class MyIntentRecognizer:
        def recognize(self, text: str) -> StageResult:
            # Implementation
            return StageResult(success=True, confidence=0.95, ...)
    
    # Type checking ensures compliance
    recognizer: IntentRecognizer = MyIntentRecognizer()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class StageResult:
    """Result structure returned by all pipeline stages.
    
    The validation checkpoint pattern requires that:
    - If success is False, errors MUST be non-empty.
    - If success is True, errors MUST be empty.
    - confidence should be in range [0.0, 1.0].
    
    Attributes:
        success: Whether the stage completed successfully.
        confidence: Confidence score for the result (0.0 to 1.0).
        data: Stage-specific output data.
        errors: List of error messages (empty if success is True).
        metadata: Optional additional information (timing, model version, etc.).
    """
    success: bool
    confidence: float
    data: Any = None
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.success and self.errors:
            raise ValueError("Successful result cannot have errors")
        if not self.success and not self.errors:
            raise ValueError("Failed result must have at least one error")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")
    
    @classmethod
    def failure(cls, errors: list[str], confidence: float = 0.0, 
                metadata: dict[str, Any] | None = None) -> StageResult:
        """Create a failure result."""
        return cls(
            success=False, 
            confidence=confidence, 
            errors=errors,
            metadata=metadata or {}
        )
    
    @classmethod
    def low_confidence(cls, data: Any, confidence: float,
                       metadata: dict[str, Any] | None = None) -> StageResult:
        """Create a low-confidence result requiring clarification."""
        return cls(
            success=False,
            confidence=confidence,
            data=data,
            errors=["Low confidence - clarification required"],
            metadata=metadata or {}
        )


# =============================================================================
# Stage Protocols
# =============================================================================

@runtime_checkable
class SpeechRecognizer(Protocol):
    """Protocol for speech-to-text conversion.
    
    Implementations may use:
    - Local models (Whisper, Vosk)
    - Cloud APIs (Google STT, Azure Speech)
    - Custom fine-tuned models
    """
    
    def transcribe(self, audio: bytes, language: str = "en") -> StageResult:
        """Transcribe audio to text.
        
        Args:
            audio: Raw audio bytes (WAV, MP3, etc.).
            language: ISO language code.
        
        Returns:
            StageResult with data containing:
                - text: Transcribed text
                - segments: Optional word-level timestamps
        """
        ...


@runtime_checkable
class IntentRecognizer(Protocol):
    """Protocol for intent classification.
    
    Maps natural language input to one of the defined intents
    from the taxonomy (e.g., SET_RATE, ADD_WELL, RUN_SIMULATION).
    """
    
    def recognize(self, text: str) -> StageResult:
        """Recognize user intent from text.
        
        Args:
            text: Natural language input.
        
        Returns:
            StageResult with data containing:
                - intent: Intent identifier (e.g., "SET_RATE")
                - category: Intent category (e.g., "well_operations")
                - alternatives: List of (intent, confidence) tuples
        """
        ...


@runtime_checkable
class EntityExtractor(Protocol):
    """Protocol for entity extraction.
    
    Extracts structured entities (wells, rates, dates, etc.) from
    natural language, guided by the recognized intent.
    """
    
    def extract(self, text: str, intent: str) -> StageResult:
        """Extract entities from text given an intent.
        
        Args:
            text: Natural language input.
            intent: Recognized intent identifier.
        
        Returns:
            StageResult with data containing:
                - entities: Dict mapping entity names to values
                - missing: List of required but missing entities
                - ambiguous: List of entities with multiple interpretations
        """
        ...


@runtime_checkable
class AssetValidator(Protocol):
    """Protocol for asset context validation.
    
    Validates extracted entities against the asset database
    (e.g., checking that well names exist, grid coordinates are valid).
    """
    
    def validate(self, entities: dict[str, Any], asset_id: str) -> StageResult:
        """Validate entities against asset context.
        
        Args:
            entities: Extracted entities.
            asset_id: Identifier for the target asset/model.
        
        Returns:
            StageResult with data containing:
                - validated_entities: Entities with resolved references
                - warnings: Non-fatal validation warnings
        """
        ...


@runtime_checkable
class SyntaxGenerator(Protocol):
    """Protocol for simulation syntax generation.
    
    Generates simulator-specific syntax (ECLIPSE, OPM) from
    validated intent and entities.
    """
    
    def generate(self, intent: str, entities: dict[str, Any],
                 target_format: str = "eclipse") -> StageResult:
        """Generate simulation syntax.
        
        Args:
            intent: Validated intent identifier.
            entities: Validated entities.
            target_format: Target syntax format ("eclipse", "opm").
        
        Returns:
            StageResult with data containing:
                - syntax: Generated keyword syntax string
                - keywords: List of keywords used
                - insertions: Suggested deck insertion points
        """
        ...


@runtime_checkable
class DeckValidator(Protocol):
    """Protocol for deck validation.
    
    Validates generated syntax for both syntactic correctness
    and physics consistency.
    """
    
    def validate(self, syntax: str, context: str | None = None) -> StageResult:
        """Validate generated syntax.
        
        Args:
            syntax: Generated simulation syntax.
            context: Optional surrounding deck context.
        
        Returns:
            StageResult with data containing:
                - valid: Whether syntax is valid
                - syntax_errors: List of syntax issues
                - physics_warnings: List of physics concerns
        """
        ...


# =============================================================================
# Pipeline Controller
# =============================================================================

@runtime_checkable
class PipelineController(Protocol):
    """Protocol for the pipeline orchestrator.
    
    Coordinates the multi-stage pipeline, handling validation
    checkpoints and failure recovery.
    """
    
    def process(self, input_data: Any, input_type: str = "text") -> StageResult:
        """Process input through the full pipeline.
        
        Args:
            input_data: Input (audio bytes for speech, string for text).
            input_type: Type of input ("audio", "text").
        
        Returns:
            StageResult with data containing the final validated syntax
            or intermediate results if clarification is needed.
        """
        ...
    
    def get_stage_results(self) -> dict[str, StageResult]:
        """Get results from each completed stage.
        
        Returns:
            Dict mapping stage names to their results.
        """
        ...


# =============================================================================
# Convenience Type Aliases
# =============================================================================

# Common entity types
WellName = str
Rate = float
Pressure = float
Date = str  # ISO format


__all__ = [
    # Core types
    "StageResult",
    # Stage protocols
    "SpeechRecognizer",
    "IntentRecognizer", 
    "EntityExtractor",
    "AssetValidator",
    "SyntaxGenerator",
    "DeckValidator",
    "PipelineController",
    # Type aliases
    "WellName",
    "Rate",
    "Pressure",
    "Date",
]