"""
Intent Parser Module - Parses transcribed text into structured intents using LLM.
"""

import json
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class IntentType(Enum):
    """Supported voice command intents."""
    VISUALIZE_PROPERTY = "visualize_property"
    QUERY_VALUE = "query_value"
    MODIFY_PARAMETER = "modify_parameter"
    RUN_SIMULATION = "run_simulation"
    RUN_SENSITIVITY = "run_sensitivity"
    EXPORT_RESULTS = "export_results"
    NAVIGATE = "navigate"
    HELP = "help"
    UNDO = "undo"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Parsed intent from voice command."""
    type: IntentType
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    clarification_needed: Optional[str] = None
    
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.9
    
    def needs_confirmation(self) -> bool:
        return 0.7 <= self.confidence < 0.9
    
    def needs_clarification(self) -> bool:
        return self.confidence < 0.7 or self.clarification_needed is not None


PHASE1_INTENTS = [
    IntentType.VISUALIZE_PROPERTY,
    IntentType.QUERY_VALUE,
    IntentType.NAVIGATE,
    IntentType.HELP,
    IntentType.CANCEL,
]


INTENT_PARSER_PROMPT = """
You are a reservoir simulation assistant. Parse the user's voice command.

Available intents: visualize_property, query_value, navigate, help, cancel

Domain vocabulary:
- Properties: permeability, porosity, water saturation (Sw), oil saturation (So), pressure, BHP
- Rates: oil rate (FOPR), water rate (FWPR), water cut (FWCT)
- Wells: producer, injector, PROD1, INJ1-4
- Views: 3D, cross-section, layer, animation

User said: "{text}"

Respond with JSON only:
{{"intent": "...", "confidence": 0.0-1.0, "slots": {{...}}, "clarification_needed": null}}
"""


class IntentParser:
    """Parse voice transcriptions into structured intents."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._prompt_template = INTENT_PARSER_PROMPT
    
    async def parse(self, text: str) -> Intent:
        """Parse transcribed text into an Intent."""
        if not text.strip():
            return Intent(type=IntentType.UNKNOWN, confidence=0.0, raw_text=text)
        
        quick_intent = self._quick_match(text.lower())
        if quick_intent:
            return quick_intent
        
        return await self._llm_parse(text)
    
    def _quick_match(self, text: str) -> Optional[Intent]:
        """Quick pattern matching for common commands."""
        if text in ["stop", "cancel", "never mind", "abort"]:
            return Intent(type=IntentType.CANCEL, confidence=1.0, raw_text=text)
        
        if text in ["yes", "yeah", "yep", "confirm", "ok", "okay", "do it"]:
            return Intent(type=IntentType.CONFIRM, confidence=1.0, raw_text=text)
        
        if text.startswith("help") or "what can" in text or "how do i" in text:
            return Intent(type=IntentType.HELP, confidence=0.95, raw_text=text)
        
        return None
    
    async def _llm_parse(self, text: str) -> Intent:
        """Parse using LLM."""
        prompt = self._prompt_template.format(text=text)
        # TODO: Call LLM API
        raise NotImplementedError("LLM parsing not yet implemented")
