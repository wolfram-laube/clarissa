"""Intent Recognition Stage Implementation.

Provides multiple implementations of the IntentRecognizer protocol:
1. RuleBasedRecognizer - Keyword matching for fast, predictable results
2. LLMRecognizer - LLM-based for complex/ambiguous inputs (placeholder)
3. HybridRecognizer - Rules first, LLM fallback

Usage:
    from clarissa.agent.pipeline.intent import HybridRecognizer
    
    recognizer = HybridRecognizer()
    result = recognizer.recognize("Set well PROD-01 rate to 500 bbl/day")
    
    if result.success:
        print(f"Intent: {result.data['intent']} ({result.confidence:.0%})")
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clarissa.agent.pipeline.protocols import IntentRecognizer, StageResult


# Load taxonomy
TAXONOMY_PATH = Path(__file__).parent.parent / "intents" / "taxonomy.json"


def load_taxonomy() -> dict:
    """Load intent taxonomy from JSON file."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


@dataclass
class IntentMatch:
    """Represents a potential intent match."""
    intent: str
    category: str
    confidence: float
    matched_keywords: list[str]


class RuleBasedRecognizer:
    """Rule-based intent recognition using keyword matching.
    
    Fast and predictable, suitable for common patterns.
    Low confidence for ambiguous or complex inputs.
    
    Attributes:
        taxonomy: Loaded intent taxonomy.
        keyword_patterns: Compiled regex patterns per intent.
        confidence_threshold: Minimum confidence to return success.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize with taxonomy and build keyword patterns.
        
        Args:
            confidence_threshold: Minimum confidence for success (default 0.7).
        """
        self.taxonomy = load_taxonomy()
        self.confidence_threshold = confidence_threshold
        self.keyword_patterns = self._build_patterns()
    
    def _build_patterns(self) -> dict[str, list[re.Pattern]]:
        """Build regex patterns from taxonomy examples and keywords."""
        patterns = {}
        
        # Intent-specific keyword patterns
        intent_keywords = {
            # Simulation control
            "RUN_SIMULATION": [
                r"\b(run|start|execute|begin|launch)\b.*\b(simulation|model|case|run)\b",
                r"\b(execute|run)\b\s+[A-Z][A-Z0-9_-]*",
                r"\b(simulation|model)\b.*\b(run|start|execute)\b",
            ],
            "STOP_SIMULATION": [
                r"\b(stop|halt|abort|cancel|terminate)\b.*\b(simulation|run|model)\b",
                r"\b(simulation|run)\b.*\b(stop|abort|cancel)\b",
            ],
            "RESTART_SIMULATION": [
                r"\b(restart|resume|continue)\b.*\b(simulation|from|run)\b",
                r"\b(from checkpoint|from restart)\b",
            ],
            
            # Well operations
            "ADD_WELL": [
                r"\b(add|create|define|new)\b.*\b(well|producer|injector)\b",
                r"\b(well|producer|injector)\b.*\b(add|create|new)\b",
            ],
            "MODIFY_WELL": [
                r"\b(modify|change|update|edit)\b.*\b(well|completion|perforation)\b",
                r"\b(well)\b.*\b(modify|change|update)\b",
            ],
            "SHUT_WELL": [
                r"\b(shut|close|shut-in|shutin)\b.*\b(well|producer|injector)\b",
                r"\b(shut|close)\b\s+[A-Z][A-Z0-9_-]*\d+",
                r"\b(well)\b.*\b(shut|close)\b",
            ],
            "OPEN_WELL": [
                r"\b(open|reopen|bring online)\b.*\b(well|producer|injector)\b",
                r"\b(well)\b.*\b(open|online)\b",
            ],
            "SET_RATE": [
                r"\b(set|change|modify|limit)\b.*\b(rate|production|injection)\b",
                r"\b(rate)\b.*\b(to|at|=)\b.*\d+",
                r"\b(oil|water|gas|liquid)\b.*\b(rate)\b.*\d+",
                r"\d+\s*(stb|bbl|mscf|mmscf|m3)\s*/\s*(day|d)\b",
            ],
            "SET_PRESSURE": [
                r"\b(set|change|modify)\b.*\b(pressure|bhp|thp)\b",
                r"\b(bhp|thp|bottomhole|tubing head)\b.*\b(to|at|=)\b.*\d+",
                r"\b(pressure)\b.*\d+\s*(psi|psia|bar|kpa)\b",
            ],
            
            # Schedule operations
            "SET_DATE": [
                r"\b(advance|set|move)\b.*\b(date|to|forward)\b.*\d{4}",
                r"\b(to|until)\b.*\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
                r"\d{4}-\d{2}-\d{2}",
            ],
            "ADD_TIMESTEP": [
                r"\b(add|insert|create)\b.*\b(timestep|time step|report)\b",
                r"\d+\s*(day|month|year)\s*timestep",
            ],
            "MODIFY_SCHEDULE": [
                r"\b(modify|change|update)\b.*\b(schedule|timeline)\b",
            ],
            
            # Query operations
            "GET_PRODUCTION": [
                r"\b(show|get|what|display)\b.*\b(production|rate|output)\b",
                r"\b(oil|water|gas)\b.*\b(production|rate)\b",
                r"\b(cumulative|total)\b.*\b(production)\b",
            ],
            "GET_PRESSURE": [
                r"\b(show|get|what|display)\b.*\b(pressure)\b",
                r"\b(reservoir|average|field)\b.*\b(pressure)\b",
                r"\b(bhp|thp)\b.*\b(history|for|of)\b",
            ],
            "COMPARE_SCENARIOS": [
                r"\b(compare|difference|delta|versus|vs)\b.*\b(scenario|case|run)\b",
                r"\b(scenario|case)\b.*\b(compare|vs|versus)\b",
            ],
            "GET_SUMMARY": [
                r"\b(show|get|give)\b.*\b(summary|overview|highlights|results)\b",
                r"\b(what are)\b.*\b(results|key)\b",
            ],
            
            # Validation
            "VALIDATE_DECK": [
                r"\b(validate|check|verify)\b.*\b(deck|input|syntax)\b",
                r"\b(syntax|input)\b.*\b(error|correct|valid)\b",
            ],
            "CHECK_PHYSICS": [
                r"\b(check|verify)\b.*\b(physics|material balance|pvt|initialization)\b",
                r"\b(physics|material balance)\b.*\b(consistent|correct)\b",
            ],
            "PREVIEW_CHANGES": [
                r"\b(preview|show|what would)\b.*\b(change|do|happen)\b",
                r"\b(show|display)\b.*\b(diff|modification)\b",
            ],
            
            # Help
            "GET_HELP": [
                r"\b(help|how|what does|explain)\b.*\b(with|do|mean)\b",
                r"\b(documentation|docs|manual)\b",
            ],
            "EXPLAIN_ERROR": [
                r"\b(what|explain|why)\b.*\b(error|warning|fail)\b",
                r"\b(error|warning)\b.*\b(mean|cause)\b",
            ],
            "SUGGEST_FIX": [
                r"\b(how|suggest|recommend)\b.*\b(fix|solve|resolve)\b",
                r"\b(what should|suggestion)\b",
            ],
        }
        
        for intent, keyword_list in intent_keywords.items():
            patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in keyword_list
            ]
        
        return patterns
    
    def _get_category(self, intent: str) -> str:
        """Get category for an intent."""
        for cat_name, cat_data in self.taxonomy["categories"].items():
            if intent in cat_data["intents"]:
                return cat_name
        return "unknown"
    
    def _calculate_confidence(self, text: str, intent: str, 
                              matches: list[str]) -> float:
        """Calculate confidence score based on matches and text properties."""
        if not matches:
            return 0.0
        
        # Base confidence from number of pattern matches
        base_confidence = min(0.5 + (len(matches) * 0.15), 0.85)
        
        # Boost for shorter, more specific queries
        word_count = len(text.split())
        if word_count <= 5:
            base_confidence += 0.1
        elif word_count > 15:
            base_confidence -= 0.1
        
        # Check against taxonomy threshold
        intent_data = None
        for cat_data in self.taxonomy["categories"].values():
            if intent in cat_data["intents"]:
                intent_data = cat_data["intents"][intent]
                break
        
        if intent_data:
            # Slight penalty if below taxonomy threshold
            tax_threshold = intent_data.get("confidence_threshold", 0.85)
            if base_confidence < tax_threshold:
                base_confidence *= 0.95
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def recognize(self, text: str) -> StageResult:
        """Recognize intent from text using keyword patterns.
        
        Args:
            text: Natural language input.
        
        Returns:
            StageResult with intent classification.
        """
        text = text.strip()
        if not text:
            return StageResult.failure(["Empty input text"])
        
        matches: list[IntentMatch] = []
        
        for intent, patterns in self.keyword_patterns.items():
            matched_patterns = []
            for pattern in patterns:
                if pattern.search(text):
                    matched_patterns.append(pattern.pattern)
            
            if matched_patterns:
                confidence = self._calculate_confidence(text, intent, matched_patterns)
                matches.append(IntentMatch(
                    intent=intent,
                    category=self._get_category(intent),
                    confidence=confidence,
                    matched_keywords=matched_patterns
                ))
        
        if not matches:
            return StageResult.low_confidence(
                data={"text": text, "alternatives": []},
                confidence=0.0,
                metadata={"recognizer": "rule_based", "reason": "no_pattern_match"}
            )
        
        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)
        best_match = matches[0]
        
        # Build alternatives list
        alternatives = [
            {"intent": m.intent, "confidence": m.confidence}
            for m in matches[1:4]  # Top 3 alternatives
        ]
        
        if best_match.confidence < self.confidence_threshold:
            return StageResult.low_confidence(
                data={
                    "intent": best_match.intent,
                    "category": best_match.category,
                    "alternatives": alternatives,
                },
                confidence=best_match.confidence,
                metadata={
                    "recognizer": "rule_based",
                    "matched_patterns": best_match.matched_keywords,
                }
            )
        
        return StageResult(
            success=True,
            confidence=best_match.confidence,
            data={
                "intent": best_match.intent,
                "category": best_match.category,
                "alternatives": alternatives,
            },
            metadata={
                "recognizer": "rule_based",
                "matched_patterns": best_match.matched_keywords,
            }
        )


class LLMRecognizer:
    """LLM-based intent recognition.
    
    Uses a language model for complex or ambiguous inputs.
    Placeholder implementation - actual LLM integration TBD.
    """
    
    def __init__(self, model: str = "claude-3-haiku", 
                 confidence_threshold: float = 0.8):
        """Initialize LLM recognizer.
        
        Args:
            model: Model identifier for LLM backend.
            confidence_threshold: Minimum confidence for success.
        """
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.taxonomy = load_taxonomy()
    
    def recognize(self, text: str) -> StageResult:
        """Recognize intent using LLM.
        
        Note: This is a placeholder. Actual implementation would:
        1. Build prompt with taxonomy context
        2. Call LLM API
        3. Parse structured response
        
        Args:
            text: Natural language input.
        
        Returns:
            StageResult with intent classification.
        """
        # Placeholder - would call actual LLM
        return StageResult.failure(
            ["LLM recognizer not yet implemented"],
            metadata={"recognizer": "llm", "model": self.model}
        )


class HybridRecognizer:
    """Hybrid intent recognizer combining rules and LLM.
    
    Strategy:
    1. Try rule-based recognition first (fast, predictable)
    2. If low confidence, fall back to LLM (slower, more capable)
    3. Return best result with source indicated
    
    This is the recommended recognizer for production use.
    """
    
    def __init__(self, 
                 rule_threshold: float = 0.75,
                 llm_threshold: float = 0.8,
                 llm_model: str = "claude-3-haiku"):
        """Initialize hybrid recognizer.
        
        Args:
            rule_threshold: Confidence threshold for rule-based success.
            llm_threshold: Confidence threshold for LLM fallback.
            llm_model: Model to use for LLM fallback.
        """
        self.rule_recognizer = RuleBasedRecognizer(confidence_threshold=rule_threshold)
        self.llm_recognizer = LLMRecognizer(model=llm_model, 
                                            confidence_threshold=llm_threshold)
        self.rule_threshold = rule_threshold
    
    def recognize(self, text: str) -> StageResult:
        """Recognize intent using hybrid approach.
        
        Args:
            text: Natural language input.
        
        Returns:
            StageResult with intent classification.
        """
        # Try rules first
        rule_result = self.rule_recognizer.recognize(text)
        
        # If rules succeeded with good confidence, use that
        if rule_result.success and rule_result.confidence >= self.rule_threshold:
            return rule_result
        
        # If rules got something but low confidence, try LLM
        if rule_result.confidence > 0:
            llm_result = self.llm_recognizer.recognize(text)
            
            # If LLM succeeded, prefer it
            if llm_result.success:
                return llm_result
            
            # Otherwise return rule result (even if low confidence)
            # Better to have something than nothing
            return rule_result
        
        # Rules found nothing, try LLM as last resort
        llm_result = self.llm_recognizer.recognize(text)
        if llm_result.success:
            return llm_result
        
        # Nothing worked
        return StageResult.failure(
            ["Could not recognize intent from input"],
            metadata={"recognizer": "hybrid", "tried": ["rule_based", "llm"]}
        )


# Convenience function
def create_recognizer(mode: str = "hybrid", **kwargs) -> IntentRecognizer:
    """Factory function to create intent recognizers.
    
    Args:
        mode: One of "rules", "llm", or "hybrid" (default).
        **kwargs: Additional arguments passed to recognizer constructor.
    
    Returns:
        IntentRecognizer implementation.
    """
    recognizers = {
        "rules": RuleBasedRecognizer,
        "llm": LLMRecognizer,
        "hybrid": HybridRecognizer,
    }
    
    if mode not in recognizers:
        raise ValueError(f"Unknown mode: {mode}. Use one of {list(recognizers.keys())}")
    
    return recognizers[mode](**kwargs)


__all__ = [
    "RuleBasedRecognizer",
    "LLMRecognizer", 
    "HybridRecognizer",
    "create_recognizer",
    "IntentMatch",
]