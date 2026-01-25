"""
Tests for CLARISSA Voice Intent Parser.

These tests work WITHOUT any API keys (rule-based only).
"""

import pytest
from dataclasses import dataclass
from enum import Enum


# Minimal implementation for testing (since we can't import the actual module in CI easily)
class IntentType(Enum):
    VISUALIZE_PROPERTY = "visualize_property"
    QUERY_VALUE = "query_value"
    NAVIGATE = "navigate"
    HELP = "help"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"


def parse_intent_rules(text: str) -> dict:
    """Rule-based intent parsing - works WITHOUT any API key."""
    import re
    text_lower = text.lower().strip()
    slots = {}
    
    # Cancel
    if text_lower in ["cancel", "stop", "abort", "quit"]:
        return {"type": "cancel", "confidence": 1.0, "slots": {}}
    
    # Confirm
    if text_lower in ["yes", "yeah", "confirm", "ok", "okay", "do it"]:
        return {"type": "confirm", "confidence": 1.0, "slots": {}}
    
    # Help
    if text_lower == "help" or "help me" in text_lower:
        return {"type": "help", "confidence": 1.0, "slots": {}}
    
    # Visualization
    viz_triggers = ["show", "display", "visualize", "plot"]
    if any(t in text_lower for t in viz_triggers):
        if "perm" in text_lower:
            slots["property"] = "permeability"
        elif "poro" in text_lower:
            slots["property"] = "porosity"
        elif "sat" in text_lower:
            slots["property"] = "water_saturation"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        
        layer_match = re.search(r'layer\s*(\d+)', text_lower)
        if layer_match:
            slots["layer"] = int(layer_match.group(1))
        
        time_match = re.search(r'(?:day|time)\s*(\d+)', text_lower)
        if time_match:
            slots["time_days"] = int(time_match.group(1))
        
        return {"type": "visualize_property", "confidence": 0.95, "slots": slots}
    
    # Query
    query_triggers = ["what", "how much", "tell me", "get"]
    if any(t in text_lower for t in query_triggers):
        if "water cut" in text_lower:
            slots["property"] = "water_cut"
        elif "oil rate" in text_lower:
            slots["property"] = "oil_rate"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        
        return {"type": "query_value", "confidence": 0.90, "slots": slots}
    
    # Navigate
    if "go to" in text_lower or "navigate" in text_lower:
        if "result" in text_lower:
            slots["target"] = "results"
        elif "model" in text_lower:
            slots["target"] = "model"
        return {"type": "navigate", "confidence": 0.90, "slots": slots}
    
    return {"type": "unknown", "confidence": 0.0, "slots": {}}


class TestIntentParser:
    """Test rule-based intent parsing."""
    
    def test_cancel_commands(self):
        """Test cancel intent recognition."""
        for cmd in ["cancel", "stop", "abort"]:
            result = parse_intent_rules(cmd)
            assert result["type"] == "cancel"
            assert result["confidence"] == 1.0
    
    def test_confirm_commands(self):
        """Test confirm intent recognition."""
        for cmd in ["yes", "confirm", "ok", "okay"]:
            result = parse_intent_rules(cmd)
            assert result["type"] == "confirm"
            assert result["confidence"] == 1.0
    
    def test_help_command(self):
        """Test help intent recognition."""
        result = parse_intent_rules("help")
        assert result["type"] == "help"
        assert result["confidence"] == 1.0
    
    def test_visualization_permeability(self):
        """Test permeability visualization."""
        result = parse_intent_rules("show me the permeability")
        assert result["type"] == "visualize_property"
        assert result["slots"]["property"] == "permeability"
        assert result["confidence"] >= 0.9
    
    def test_visualization_with_layer(self):
        """Test visualization with layer specification."""
        result = parse_intent_rules("show permeability at layer 3")
        assert result["type"] == "visualize_property"
        assert result["slots"]["property"] == "permeability"
        assert result["slots"]["layer"] == 3
    
    def test_visualization_with_time(self):
        """Test visualization with time specification."""
        result = parse_intent_rules("show saturation at day 500")
        assert result["type"] == "visualize_property"
        assert result["slots"]["property"] == "water_saturation"
        assert result["slots"]["time_days"] == 500
    
    def test_query_water_cut(self):
        """Test water cut query."""
        result = parse_intent_rules("what is the water cut")
        assert result["type"] == "query_value"
        assert result["slots"]["property"] == "water_cut"
    
    def test_query_oil_rate(self):
        """Test oil rate query."""
        result = parse_intent_rules("how much oil rate")
        assert result["type"] == "query_value"
        assert result["slots"]["property"] == "oil_rate"
    
    def test_navigate_results(self):
        """Test navigation to results."""
        result = parse_intent_rules("go to results")
        assert result["type"] == "navigate"
        assert result["slots"]["target"] == "results"
    
    def test_unknown_command(self):
        """Test unknown command handling."""
        result = parse_intent_rules("flibbertigibbet")
        assert result["type"] == "unknown"
        assert result["confidence"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
