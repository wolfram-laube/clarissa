"""
Intent parsing module for CLARISSA voice interface.

Supports multiple LLM backends:
- Claude (Anthropic) - CLARISSA's native LLM
- GPT-4 (OpenAI) - Fallback option
- Rule-based - Works without any API key

Priority: Rules → Claude → GPT-4 → Unknown
"""

import os
import re
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable


class IntentType(Enum):
    """Supported voice command intents."""
    
    # Visualization
    VISUALIZE_PROPERTY = "visualize_property"
    
    # Data queries
    QUERY_VALUE = "query_value"
    
    # Model modification
    MODIFY_PARAMETER = "modify_parameter"
    
    # Simulation control
    RUN_SIMULATION = "run_simulation"
    RUN_SENSITIVITY = "run_sensitivity"
    
    # Results
    EXPORT_RESULTS = "export_results"
    
    # Navigation
    NAVIGATE = "navigate"
    
    # Meta
    HELP = "help"
    UNDO = "undo"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    
    # Fallback
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Parsed intent from voice command."""
    
    type: IntentType
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    clarification_needed: bool = False
    clarification_prompt: Optional[str] = None
    parse_method: str = "unknown"  # "rules", "claude", "openai"
    
    def needs_confirmation(self) -> bool:
        """Check if this intent requires user confirmation."""
        dangerous_intents = {
            IntentType.MODIFY_PARAMETER,
            IntentType.RUN_SIMULATION,
            IntentType.RUN_SENSITIVITY,
        }
        return self.type in dangerous_intents and self.confidence < 0.95


# Domain vocabulary for better recognition
DOMAIN_VOCABULARY = """
Reservoir simulation terms: permeability, porosity, water saturation (Sw),
oil saturation (So), pressure, BHP, bottomhole pressure, OOIP, STOIIP,
waterflood, injector, producer, PROD1, INJ1, INJ2, INJ3, INJ4,
millidarcy, mD, psi, bar, bbl/day, STB, FOPT, FOPR, FWPT, FWPR, FWCT,
water cut, GOR, gas-oil ratio, layer, grid, cell, timestep, 
3D visualization, cross-section, animation, time-lapse
"""

INTENT_SYSTEM_PROMPT = """You are a reservoir simulation assistant parsing voice commands.

Available intents:
- visualize_property: Show reservoir properties (permeability, porosity, saturation, pressure)
- query_value: Ask about simulation values (rates, pressures, water cut, cumulative)
- modify_parameter: Change model parameters
- run_simulation: Execute a simulation run
- run_sensitivity: Run sensitivity analysis
- export_results: Export data or images
- navigate: Go to different sections
- help: Request assistance
- undo: Revert last action
- confirm: Confirm pending action
- cancel: Cancel current action

Extract slots:
- property: permeability, porosity, water_saturation, oil_saturation, pressure
- layer: integer (1-20)
- time_days: integer
- view_type: 3d, cross_section_xy, cross_section_xz, animation
- well: well name (PROD1, INJ1, etc.)
- value: numeric value for modifications
- unit: unit of measurement
- target: navigation target

Respond with ONLY valid JSON:
{"intent": "<type>", "confidence": <0.0-1.0>, "slots": {...}}"""


class IntentParser:
    """
    Multi-backend intent parser for CLARISSA.
    
    Supports Claude (Anthropic), GPT-4 (OpenAI), and rule-based parsing.
    """
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.90
    MEDIUM_CONFIDENCE = 0.70
    LOW_CONFIDENCE = 0.50
    
    def __init__(
        self,
        prefer_claude: bool = True,
        enable_rules: bool = True,
        anthropic_model: str = "claude-sonnet-4-20250514",
        openai_model: str = "gpt-4o-mini",
    ):
        """
        Initialize the intent parser.
        
        Args:
            prefer_claude: Use Claude over GPT-4 when both available
            enable_rules: Enable rule-based parsing (recommended)
            anthropic_model: Claude model to use
            openai_model: OpenAI model to use
        """
        self.prefer_claude = prefer_claude
        self.enable_rules = enable_rules
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model
        
        # Check available backends
        self.anthropic_available = bool(os.getenv('ANTHROPIC_API_KEY'))
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        
    def get_available_backends(self) -> List[str]:
        """Return list of available parsing backends."""
        backends = []
        if self.enable_rules:
            backends.append("rules")
        if self.anthropic_available:
            backends.append("claude")
        if self.openai_available:
            backends.append("openai")
        return backends
    
    async def parse(self, text: str) -> Intent:
        """
        Parse text into structured intent.
        
        Priority:
        1. Rule-based (instant, no API)
        2. Claude (CLARISSA native)
        3. OpenAI GPT-4 (fallback)
        
        Args:
            text: Transcribed voice command
            
        Returns:
            Parsed Intent object
        """
        # Try rule-based first
        if self.enable_rules:
            result = self._parse_with_rules(text)
            if result is not None:
                return result
        
        # Try Claude
        if self.anthropic_available and self.prefer_claude:
            try:
                return await self._parse_with_claude(text)
            except Exception as e:
                print(f"Claude parsing failed: {e}")
        
        # Try OpenAI
        if self.openai_available:
            try:
                return await self._parse_with_openai(text)
            except Exception as e:
                print(f"OpenAI parsing failed: {e}")
        
        # Try Claude as last resort if not preferred but available
        if self.anthropic_available and not self.prefer_claude:
            try:
                return await self._parse_with_claude(text)
            except Exception as e:
                print(f"Claude fallback failed: {e}")
        
        # No backend available or all failed
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            raw_text=text,
            parse_method="none",
            clarification_needed=True,
            clarification_prompt="I couldn't understand that. Could you rephrase?"
        )
    
    def parse_sync(self, text: str) -> Intent:
        """Synchronous version of parse()."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.parse(text))
    
    def _parse_with_rules(self, text: str) -> Optional[Intent]:
        """
        Rule-based intent parsing - works WITHOUT any API key.
        
        Handles common reservoir simulation commands with regex patterns.
        """
        text_lower = text.lower().strip()
        slots: Dict[str, Any] = {}
        
        # === HIGH PRIORITY: Control commands ===
        
        # Cancel
        cancel_patterns = ["stop", "cancel", "never mind", "abort", "quit", "exit"]
        if text_lower in cancel_patterns or text_lower.startswith("cancel"):
            return Intent(IntentType.CANCEL, 1.0, {}, text, parse_method="rules")
        
        # Confirm
        confirm_patterns = ["yes", "yeah", "yep", "confirm", "ok", "okay", 
                          "do it", "go ahead", "proceed", "affirmative"]
        if text_lower in confirm_patterns:
            return Intent(IntentType.CONFIRM, 1.0, {}, text, parse_method="rules")
        
        # Help
        if text_lower == "help" or text_lower.startswith("what can") or \
           text_lower.startswith("how do i") or "help me" in text_lower:
            return Intent(IntentType.HELP, 1.0, {}, text, parse_method="rules")
        
        # Undo
        if text_lower in ["undo", "go back", "revert", "undo that"]:
            return Intent(IntentType.UNDO, 1.0, {}, text, parse_method="rules")
        
        # === VISUALIZATION ===
        
        viz_triggers = ["show", "display", "visualize", "plot", "view", 
                       "see", "render", "draw"]
        is_viz = any(trigger in text_lower for trigger in viz_triggers)
        
        if is_viz:
            # Property extraction
            if "perm" in text_lower:
                slots["property"] = "permeability"
            elif "poro" in text_lower:
                slots["property"] = "porosity"
            elif any(x in text_lower for x in ["saturation", " sw ", "water sat"]):
                slots["property"] = "water_saturation"
            elif any(x in text_lower for x in ["pressure", "bhp"]):
                slots["property"] = "pressure"
            elif "oil sat" in text_lower or " so " in text_lower:
                slots["property"] = "oil_saturation"
            
            # Layer extraction
            layer_match = re.search(r'layer\s*(\d+)', text_lower)
            if layer_match:
                slots["layer"] = int(layer_match.group(1))
            
            # Time extraction
            time_patterns = [
                r'(?:day|time|t\s*=?\s*)(\d+)',
                r'at\s+(\d+)\s*(?:days?)?',
                r'(\d+)\s*days?'
            ]
            for pattern in time_patterns:
                time_match = re.search(pattern, text_lower)
                if time_match:
                    slots["time_days"] = int(time_match.group(1))
                    break
            
            # View type
            if "3d" in text_lower or "cube" in text_lower or "volume" in text_lower:
                slots["view_type"] = "3d"
            elif any(x in text_lower for x in ["cross", "section", "slice", "xy"]):
                slots["view_type"] = "cross_section_xy"
            elif any(x in text_lower for x in ["xz", "vertical"]):
                slots["view_type"] = "cross_section_xz"
            elif "animat" in text_lower or "movie" in text_lower:
                slots["view_type"] = "animation"
            
            # Default property if only layer specified
            if "property" not in slots and "layer" not in slots:
                slots["property"] = "permeability"
            
            confidence = 0.95 if slots else 0.80
            return Intent(IntentType.VISUALIZE_PROPERTY, confidence, slots, 
                         text, parse_method="rules")
        
        # === QUERIES ===
        
        query_triggers = ["what", "how much", "tell me", "get", "current", 
                         "value of", "show me the value"]
        is_query = any(trigger in text_lower for trigger in query_triggers)
        
        if is_query:
            if any(x in text_lower for x in ["oil rate", "fopr", "oil production"]):
                slots["property"] = "oil_rate"
            elif any(x in text_lower for x in ["water rate", "fwpr", "water production"]):
                slots["property"] = "water_rate"
            elif any(x in text_lower for x in ["water cut", "fwct", "wct"]):
                slots["property"] = "water_cut"
            elif any(x in text_lower for x in ["gas rate", "fgpr"]):
                slots["property"] = "gas_rate"
            elif any(x in text_lower for x in ["pressure", "bhp", "fpr"]):
                slots["property"] = "pressure"
            elif any(x in text_lower for x in ["cumulative", "total", "fopt", "cum"]):
                slots["property"] = "cumulative_oil"
            elif "gor" in text_lower or "gas oil" in text_lower:
                slots["property"] = "gor"
            
            # Well extraction
            well_match = re.search(r'((?:prod|inj|well)[_\s]?\d+)', text_lower)
            if well_match:
                slots["well"] = well_match.group(1).upper().replace(" ", "")
            
            if slots:
                return Intent(IntentType.QUERY_VALUE, 0.90, slots, 
                             text, parse_method="rules")
        
        # === NAVIGATION ===
        
        nav_triggers = ["go to", "navigate", "open", "back to", "switch to"]
        is_nav = any(trigger in text_lower for trigger in nav_triggers)
        
        if is_nav:
            if "result" in text_lower:
                slots["target"] = "results"
            elif "sensitiv" in text_lower:
                slots["target"] = "sensitivity"
            elif "model" in text_lower:
                slots["target"] = "model"
            elif "export" in text_lower:
                slots["target"] = "export"
            elif "grid" in text_lower:
                slots["target"] = "grid"
            elif "well" in text_lower:
                slots["target"] = "wells"
            elif "schedule" in text_lower:
                slots["target"] = "schedule"
            
            if slots:
                return Intent(IntentType.NAVIGATE, 0.90, slots, 
                             text, parse_method="rules")
        
        # === RUN SIMULATION ===
        
        if any(x in text_lower for x in ["run sim", "start sim", "execute", "run the model"]):
            return Intent(IntentType.RUN_SIMULATION, 0.85, {}, text, parse_method="rules")
        
        # === EXPORT ===
        
        if any(x in text_lower for x in ["export", "save", "download"]):
            if "gif" in text_lower:
                slots["format"] = "gif"
            elif "png" in text_lower:
                slots["format"] = "png"
            elif "csv" in text_lower:
                slots["format"] = "csv"
            return Intent(IntentType.EXPORT_RESULTS, 0.85, slots, text, parse_method="rules")
        
        # No rule matched
        return None
    
    async def _parse_with_claude(self, text: str) -> Intent:
        """Parse intent using Claude (Anthropic)."""
        import anthropic
        
        client = anthropic.Anthropic()
        
        prompt = f"{INTENT_SYSTEM_PROMPT}\n\nUser said: \"{text}\"\n\nJSON response:"
        
        response = client.messages.create(
            model=self.anthropic_model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text.strip()
        return self._parse_llm_response(result_text, text, "claude")
    
    async def _parse_with_openai(self, text: str) -> Intent:
        """Parse intent using GPT-4 (OpenAI)."""
        import openai
        
        client = openai.OpenAI()
        
        response = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": f'User said: "{text}"\n\nJSON response:'}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        return self._parse_llm_response(result_text, text, "openai")
    
    def _parse_llm_response(self, response: str, original_text: str, method: str) -> Intent:
        """Parse JSON response from LLM."""
        # Clean up markdown code blocks
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()
        
        try:
            data = json.loads(response)
            
            intent_str = data.get("intent", "unknown")
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                intent_type = IntentType.UNKNOWN
            
            confidence = float(data.get("confidence", 0.8))
            slots = data.get("slots", {})
            
            return Intent(
                type=intent_type,
                confidence=confidence,
                slots=slots,
                raw_text=original_text,
                parse_method=method
            )
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=original_text,
                parse_method=method,
                clarification_needed=True,
                clarification_prompt="I had trouble understanding. Could you rephrase?"
            )


# Convenience function for quick parsing
async def parse_intent(text: str) -> Intent:
    """Quick intent parsing with default settings."""
    parser = IntentParser()
    return await parser.parse(text)


def parse_intent_sync(text: str) -> Intent:
    """Synchronous intent parsing."""
    parser = IntentParser()
    return parser.parse_sync(text)
