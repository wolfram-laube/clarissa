"""
Response generation module for CLARISSA voice interface.

Generates natural language responses and confirmation prompts.
"""

from dataclasses import dataclass
from typing import Optional, Any
from .intent import Intent, IntentType
from .execute import ExecutionResult


@dataclass
class Response:
    """Generated response for user."""
    
    text: str
    audio_url: Optional[str] = None
    action_description: Optional[str] = None
    requires_confirmation: bool = False
    visualization: Any = None


# Response templates
RESPONSE_TEMPLATES = {
    # Success responses
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
    IntentType.UNDO: {
        "success": "Undone.",
        "error": "Nothing to undo.",
    },
    
    # Generic
    "unknown": {
        "error": "I didn't understand that. Try saying 'help' for available commands.",
    },
    "clarification": "Could you clarify? {prompt}",
    "confirmation": "I'll {action}. Confirm?",
}


class ResponseGenerator:
    """
    Generates natural language responses for voice interface.
    
    Example:
        generator = ResponseGenerator()
        response = generator.generate(intent, result)
        print(response)  # "Showing permeability at layer 3."
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize response generator.
        
        Args:
            verbose: Include additional details in responses
        """
        self.verbose = verbose
    
    def generate(self, intent: Intent, result: ExecutionResult) -> str:
        """
        Generate response text.
        
        Args:
            intent: Parsed intent
            result: Execution result
            
        Returns:
            Response text
        """
        templates = RESPONSE_TEMPLATES.get(intent.type, RESPONSE_TEMPLATES["unknown"])
        
        if result.success:
            template = templates.get("success", "{description}")
        else:
            template = templates.get("error", "An error occurred. {error}")
        
        # Build template variables
        variables = {
            "property": intent.slots.get("property", "data"),
            "layer_text": "",
            "time_text": "",
            "target": intent.slots.get("target", ""),
            "format": intent.slots.get("format", "file"),
            "description": result.action_description,
            "error": result.error or "Unknown error",
            "action": self._describe_action(intent),
        }
        
        # Add layer text if present
        if intent.slots.get("layer"):
            variables["layer_text"] = f" at layer {intent.slots['layer']}"
        
        # Add time text if present
        if intent.slots.get("time_days"):
            variables["time_text"] = f" at day {intent.slots['time_days']}"
        
        try:
            return template.format(**variables)
        except KeyError:
            return result.action_description or "Done."
    
    def generate_confirmation_prompt(self, intent: Intent) -> str:
        """
        Generate confirmation prompt for dangerous actions.
        
        Args:
            intent: Intent requiring confirmation
            
        Returns:
            Confirmation prompt text
        """
        action = self._describe_action(intent)
        return f"I'll {action}. Say 'confirm' to proceed or 'cancel' to abort."
    
    def generate_clarification(self, prompt: str) -> str:
        """
        Generate clarification request.
        
        Args:
            prompt: Clarification prompt
            
        Returns:
            Clarification request text
        """
        return f"Could you clarify? {prompt}"
    
    def generate_error(self, error: str) -> str:
        """
        Generate error response.
        
        Args:
            error: Error message
            
        Returns:
            Error response text
        """
        return f"Sorry, something went wrong: {error}"
    
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
        
        elif intent.type == IntentType.MODIFY_PARAMETER:
            return f"modify {slots}"
        
        elif intent.type == IntentType.RUN_SIMULATION:
            return "run the simulation"
        
        elif intent.type == IntentType.RUN_SENSITIVITY:
            return "run sensitivity analysis"
        
        elif intent.type == IntentType.EXPORT_RESULTS:
            fmt = slots.get("format", "file")
            return f"export as {fmt.upper()}"
        
        elif intent.type == IntentType.NAVIGATE:
            target = slots.get("target", "there")
            return f"navigate to {target}"
        
        else:
            return intent.type.value.replace("_", " ")
