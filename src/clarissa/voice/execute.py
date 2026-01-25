"""
Command Executor Module - Maps intents to concrete actions.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .intent import Intent, IntentType


@dataclass
class ExecutionResult:
    """Result of command execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    visualization_url: Optional[str] = None


COMMAND_HANDLERS: Dict[IntentType, Dict] = {
    IntentType.VISUALIZE_PROPERTY: {
        "handler": "visualization_service.show_property",
        "required_slots": [],
        "optional_slots": ["property", "layer", "time_days", "view_type"],
        "defaults": {"property": "permeability", "view_type": "3d"}
    },
    IntentType.QUERY_VALUE: {
        "handler": "data_service.get_value",
        "required_slots": ["property"],
        "optional_slots": ["well", "time_days"],
    },
    IntentType.NAVIGATE: {
        "handler": "ui_service.navigate",
        "required_slots": ["target"],
    },
    IntentType.HELP: {
        "handler": "help_service.get_help",
        "optional_slots": ["topic"],
    },
    IntentType.CANCEL: {"handler": "control_service.cancel"},
    IntentType.CONFIRM: {"handler": "control_service.confirm"},
}


class CommandExecutor:
    """Execute voice commands by mapping intents to actions."""
    
    def __init__(self, visualization_service=None, data_service=None, ui_service=None):
        self.viz = visualization_service
        self.data = data_service
        self.ui = ui_service
        self._pending_intent: Optional[Intent] = None
    
    async def execute(self, intent: Intent) -> ExecutionResult:
        """Execute an intent."""
        if intent.type == IntentType.CONFIRM and self._pending_intent:
            return await self._execute_pending()
        
        if intent.type == IntentType.CANCEL:
            self._pending_intent = None
            return ExecutionResult(success=True)
        
        if intent.needs_confirmation():
            self._pending_intent = intent
            return ExecutionResult(success=True, result="confirmation_required")
        
        return await self._execute_intent(intent)
    
    async def _execute_pending(self) -> ExecutionResult:
        """Execute pending intent after confirmation."""
        if not self._pending_intent:
            return ExecutionResult(success=False, error="Nothing pending")
        intent = self._pending_intent
        self._pending_intent = None
        return await self._execute_intent(intent)
    
    async def _execute_intent(self, intent: Intent) -> ExecutionResult:
        """Execute a specific intent."""
        handler_config = COMMAND_HANDLERS.get(intent.type)
        if not handler_config:
            return ExecutionResult(success=False, error=f"No handler for {intent.type}")
        
        try:
            if intent.type == IntentType.VISUALIZE_PROPERTY:
                return await self._visualize(intent)
            elif intent.type == IntentType.QUERY_VALUE:
                return await self._query(intent)
            elif intent.type == IntentType.NAVIGATE:
                return await self._navigate(intent)
            elif intent.type == IntentType.HELP:
                return await self._help(intent)
            else:
                return ExecutionResult(success=True)
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    async def _visualize(self, intent: Intent) -> ExecutionResult:
        """Handle visualization commands."""
        slots = intent.slots
        return ExecutionResult(success=True, result={
            "property": slots.get("property", "permeability"),
            "layer": slots.get("layer"),
            "time_days": slots.get("time_days"),
            "view_type": slots.get("view_type", "3d")
        })
    
    async def _query(self, intent: Intent) -> ExecutionResult:
        return ExecutionResult(success=True, result={"value": 0, "unit": ""})
    
    async def _navigate(self, intent: Intent) -> ExecutionResult:
        return ExecutionResult(success=True, result={"target": intent.slots.get("target")})
    
    async def _help(self, intent: Intent) -> ExecutionResult:
        return ExecutionResult(success=True, result={"help": "general"})
