"""
Tests for CLARISSA Voice Response Generator.

Tests response generation for different intents and execution results.
"""

import pytest
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict


# Minimal types for testing
class IntentType(Enum):
    VISUALIZE_PROPERTY = "visualize_property"
    QUERY_VALUE = "query_value"
    NAVIGATE = "navigate"
    HELP = "help"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    EXPORT_RESULTS = "export_results"
    UNDO = "undo"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    slots: Dict[str, Any]
    raw_text: str = ""


@dataclass
class ExecutionResult:
    success: bool
    result: Any = None
    error: Optional[str] = None
    action_description: Optional[str] = None


# Response templates (mirroring respond.py)
RESPONSE_TEMPLATES = {
    IntentType.VISUALIZE_PROPERTY: {
        "success": "Showing {property}{layer_text}{time_text}.",
        "error": "Unable to visualize {property}. {error}",
    },
    IntentType.QUERY_VALUE: {
        "success": "{description}",
        "error": "Unable to get {property}. {error}",
    },
    IntentType.NAVIGATE: {
        "success": "Navigating to {target}.",
        "error": "Unable to navigate to {target}. {error}",
    },
    IntentType.HELP: {
        "success": "{description}",
    },
    IntentType.CANCEL: {
        "success": "Cancelled.",
    },
    IntentType.CONFIRM: {
        "success": "Confirmed. {description}",
        "error": "Nothing to confirm.",
    },
    IntentType.EXPORT_RESULTS: {
        "success": "Exporting as {format}...",
        "error": "Export failed. {error}",
    },
}


class ResponseGenerator:
    """Simplified response generator for testing."""

    def generate(self, intent: Intent, result: ExecutionResult) -> str:
        """Generate response text."""
        templates = RESPONSE_TEMPLATES.get(intent.type, {})

        if result.success:
            template = templates.get("success", "{description}")
        else:
            template = templates.get("error", "An error occurred. {error}")

        variables = {
            "property": intent.slots.get("property", "data"),
            "layer_text": "",
            "time_text": "",
            "target": intent.slots.get("target", ""),
            "format": intent.slots.get("format", "file"),
            "description": result.action_description or "Done.",
            "error": result.error or "Unknown error",
        }

        if intent.slots.get("layer"):
            variables["layer_text"] = f" at layer {intent.slots['layer']}"

        if intent.slots.get("time_days"):
            variables["time_text"] = f" at day {intent.slots['time_days']}"

        try:
            return template.format(**variables)
        except KeyError:
            return result.action_description or "Done."

    def generate_confirmation_prompt(self, intent: Intent) -> str:
        """Generate confirmation prompt for dangerous actions."""
        action = self._describe_action(intent)
        return f"I'll {action}. Say 'confirm' to proceed or 'cancel' to abort."

    def _describe_action(self, intent: Intent) -> str:
        """Describe the action an intent will perform."""
        slots = intent.slots

        if intent.type == IntentType.VISUALIZE_PROPERTY:
            prop = slots.get("property", "the property")
            desc = f"show {prop.replace('_', ' ')}"
            if slots.get("layer"):
                desc += f" at layer {slots['layer']}"
            return desc
        elif intent.type == IntentType.QUERY_VALUE:
            prop = slots.get("property", "the value")
            return f"get {prop.replace('_', ' ')}"
        elif intent.type == IntentType.EXPORT_RESULTS:
            fmt = slots.get("format", "file")
            return f"export as {fmt.upper()}"
        elif intent.type == IntentType.NAVIGATE:
            target = slots.get("target", "there")
            return f"navigate to {target}"
        else:
            return intent.type.value.replace("_", " ")


class TestResponseGenerator:
    """Test response generation for various intents."""

    @pytest.fixture
    def generator(self):
        return ResponseGenerator()

    def test_visualize_property_success(self, generator):
        """Test successful visualization response."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.95,
            slots={"property": "permeability"},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Showing permeability" in response
        assert "layer" not in response.lower()

    def test_visualize_with_layer(self, generator):
        """Test visualization response with layer."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.95,
            slots={"property": "porosity", "layer": 5},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Showing porosity" in response
        assert "layer 5" in response

    def test_visualize_with_time(self, generator):
        """Test visualization response with time."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.95,
            slots={"property": "water_saturation", "time_days": 100},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Showing water_saturation" in response
        assert "day 100" in response

    def test_visualize_with_layer_and_time(self, generator):
        """Test visualization response with both layer and time."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.95,
            slots={"property": "pressure", "layer": 3, "time_days": 500},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Showing pressure" in response
        assert "layer 3" in response
        assert "day 500" in response

    def test_visualize_error(self, generator):
        """Test visualization error response."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.95,
            slots={"property": "invalid_prop"},
        )
        result = ExecutionResult(success=False, error="Property not found")

        response = generator.generate(intent, result)

        assert "Unable to visualize" in response
        assert "Property not found" in response

    def test_query_value_success(self, generator):
        """Test successful query response."""
        intent = Intent(
            type=IntentType.QUERY_VALUE,
            confidence=0.90,
            slots={"property": "oil_rate"},
        )
        result = ExecutionResult(
            success=True,
            action_description="Oil rate is 1500 STB/day",
        )

        response = generator.generate(intent, result)

        assert "1500 STB/day" in response

    def test_query_value_error(self, generator):
        """Test query error response."""
        intent = Intent(
            type=IntentType.QUERY_VALUE,
            confidence=0.90,
            slots={"property": "water_cut"},
        )
        result = ExecutionResult(success=False, error="No simulation results")

        response = generator.generate(intent, result)

        assert "Unable to get" in response
        assert "No simulation results" in response

    def test_navigate_success(self, generator):
        """Test successful navigation response."""
        intent = Intent(
            type=IntentType.NAVIGATE,
            confidence=0.90,
            slots={"target": "results"},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Navigating to results" in response

    def test_cancel_response(self, generator):
        """Test cancel response."""
        intent = Intent(
            type=IntentType.CANCEL,
            confidence=1.0,
            slots={},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert response == "Cancelled."

    def test_export_success(self, generator):
        """Test export response."""
        intent = Intent(
            type=IntentType.EXPORT_RESULTS,
            confidence=0.85,
            slots={"format": "png"},
        )
        result = ExecutionResult(success=True)

        response = generator.generate(intent, result)

        assert "Exporting as png" in response

    def test_confirmation_prompt(self, generator):
        """Test confirmation prompt generation."""
        intent = Intent(
            type=IntentType.VISUALIZE_PROPERTY,
            confidence=0.85,
            slots={"property": "permeability", "layer": 5},
        )

        prompt = generator.generate_confirmation_prompt(intent)

        assert "confirm" in prompt.lower()
        assert "cancel" in prompt.lower()
        assert "permeability" in prompt


class TestResponseTemplates:
    """Test response template coverage."""

    def test_all_intents_have_success_template(self):
        """Verify all main intents have success templates."""
        required_intents = [
            IntentType.VISUALIZE_PROPERTY,
            IntentType.QUERY_VALUE,
            IntentType.NAVIGATE,
            IntentType.CANCEL,
        ]

        for intent in required_intents:
            assert intent in RESPONSE_TEMPLATES, f"Missing template for {intent}"
            assert "success" in RESPONSE_TEMPLATES[intent], f"Missing success for {intent}"

    def test_error_templates_exist_for_fallible_intents(self):
        """Verify error templates exist for intents that can fail."""
        fallible_intents = [
            IntentType.VISUALIZE_PROPERTY,
            IntentType.QUERY_VALUE,
            IntentType.NAVIGATE,
            IntentType.EXPORT_RESULTS,
        ]

        for intent in fallible_intents:
            templates = RESPONSE_TEMPLATES.get(intent, {})
            assert "error" in templates, f"Missing error template for {intent}"


class TestDynamicSlotInsertion:
    """Test dynamic slot value insertion in responses."""

    @pytest.fixture
    def generator(self):
        return ResponseGenerator()

    def test_property_slot_insertion(self, generator):
        """Test property slot is correctly inserted."""
        test_properties = ["permeability", "porosity", "water_saturation", "pressure"]

        for prop in test_properties:
            intent = Intent(
                type=IntentType.VISUALIZE_PROPERTY,
                confidence=0.95,
                slots={"property": prop},
            )
            result = ExecutionResult(success=True)

            response = generator.generate(intent, result)
            assert prop in response

    def test_layer_slot_insertion(self, generator):
        """Test layer slot is correctly inserted."""
        for layer in [1, 5, 10, 20]:
            intent = Intent(
                type=IntentType.VISUALIZE_PROPERTY,
                confidence=0.95,
                slots={"property": "permeability", "layer": layer},
            )
            result = ExecutionResult(success=True)

            response = generator.generate(intent, result)
            assert f"layer {layer}" in response

    def test_time_slot_insertion(self, generator):
        """Test time slot is correctly inserted."""
        for time in [100, 500, 1000, 3650]:
            intent = Intent(
                type=IntentType.VISUALIZE_PROPERTY,
                confidence=0.95,
                slots={"property": "porosity", "time_days": time},
            )
            result = ExecutionResult(success=True)

            response = generator.generate(intent, result)
            assert f"day {time}" in response

    def test_target_slot_insertion(self, generator):
        """Test navigation target slot is correctly inserted."""
        targets = ["results", "model", "sensitivity", "export"]

        for target in targets:
            intent = Intent(
                type=IntentType.NAVIGATE,
                confidence=0.90,
                slots={"target": target},
            )
            result = ExecutionResult(success=True)

            response = generator.generate(intent, result)
            assert target in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])