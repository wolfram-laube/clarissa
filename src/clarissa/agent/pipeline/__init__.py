"""CLARISSA NLP Pipeline Module.

Multi-stage translation pipeline per ADR-009.

Stages:
1. Speech Recognition (optional)
2. Intent Recognition
3. Entity Extraction
4. Asset Validation
5. Syntax Generation
6. Deck Validation

Each stage exposes a Protocol for testability and swappable implementations.
"""

from clarissa.agent.pipeline.protocols import (
    StageResult,
    SpeechRecognizer,
    IntentRecognizer,
    EntityExtractor,
    AssetValidator,
    SyntaxGenerator,
    DeckValidator,
    PipelineController,
)

__all__ = [
    "StageResult",
    "SpeechRecognizer",
    "IntentRecognizer",
    "EntityExtractor",
    "AssetValidator",
    "SyntaxGenerator",
    "DeckValidator",
    "PipelineController",
]
