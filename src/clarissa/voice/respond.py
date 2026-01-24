"""
Response Generator Module - Generates text responses for voice feedback.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Response:
    """Generated response for user feedback."""
    text: str
    audio_url: Optional[str] = None
    action_description: Optional[str] = None
    requires_confirmation: bool = False


RESPONSE_TEMPLATES = {
    "visualize_property": {
        "success": "Showing {property}{layer_text}{time_text}.",
        "layer_text": " at layer {layer}",
        "time_text": ", day {time_days}",
    },
    "query_value": {
        "success": "The {property} is {value} {unit}.",
        "not_found": "I couldn't find {property} data.",
    },
    "navigate": {"success": "Going to {target}."},
    "help": {"general": "You can say: 'Show me permeability', 'What is the oil rate?', or 'Go to results'."},
    "cancel": {"success": "Cancelled."},
    "confirm": {"prompt": "Did you mean to {action}? Say yes or no."},
    "clarification": {
        "property": "Which property? Permeability, porosity, or saturation?",
        "layer": "Which layer? We have layers 1 through {max_layer}.",
        "general": "I didn't quite catch that. Could you rephrase?",
    },
    "error": {
        "unknown": "I didn't understand that. Try saying 'help' for available commands.",
        "failed": "Sorry, that command failed: {error}",
    },
}


class ResponseGenerator:
    """Generate text responses for voice commands."""
    
    def __init__(self, templates: Dict = None):
        self.templates = templates or RESPONSE_TEMPLATES
    
    def success(self, intent_type: str, **kwargs) -> Response:
        """Generate success response."""
        template = self.templates.get(intent_type, {}).get("success", "Done.")
        
        if intent_type == "visualize_property":
            layer_text = self.templates[intent_type]["layer_text"].format(**kwargs) if kwargs.get("layer") else ""
            time_text = self.templates[intent_type]["time_text"].format(**kwargs) if kwargs.get("time_days") else ""
            text = template.format(property=kwargs.get("property", "property"), layer_text=layer_text, time_text=time_text)
        else:
            text = template.format(**kwargs)
        
        return Response(text=text, action_description=f"{intent_type}: {kwargs}")
    
    def clarification(self, slot_name: str, **kwargs) -> Response:
        """Generate clarification request."""
        template = self.templates["clarification"].get(slot_name, self.templates["clarification"]["general"])
        return Response(text=template.format(**kwargs), requires_confirmation=True)
    
    def error(self, error_type: str = "unknown", **kwargs) -> Response:
        """Generate error response."""
        template = self.templates["error"].get(error_type, self.templates["error"]["unknown"])
        return Response(text=template.format(**kwargs))
    
    def help(self, topic: Optional[str] = None) -> Response:
        """Generate help response."""
        return Response(text=self.templates["help"]["general"])
