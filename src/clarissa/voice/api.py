"""
CLARISSA Voice API - FastAPI Server for Browser Audio Capture.

Start with: uvicorn api:app --reload --port 8000
Open: http://localhost:8000
"""

import os
import re
import tempfile
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CLARISSA Voice API", version="0.1.0")

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IntentType(str, Enum):
    VISUALIZE_PROPERTY = "visualize_property"
    QUERY_VALUE = "query_value"
    NAVIGATE = "navigate"
    HELP = "help"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)


def parse_intent_rules(text: str) -> Intent:
    """Rule-based intent parsing - works WITHOUT any API key."""
    text_lower = text.lower().strip()
    slots = {}
    
    # Cancel
    if text_lower in ["cancel", "stop", "abort", "quit"]:
        return Intent(IntentType.CANCEL, 1.0)
    
    # Confirm
    if text_lower in ["yes", "yeah", "confirm", "ok", "okay", "do it", "yes run it"]:
        return Intent(IntentType.CONFIRM, 1.0)
    
    # Help
    if text_lower == "help" or "help me" in text_lower:
        return Intent(IntentType.HELP, 1.0)
    
    # Visualization patterns
    viz_triggers = ["show", "display", "visualize", "plot"]
    if any(t in text_lower for t in viz_triggers):
        # Property extraction
        if "perm" in text_lower:
            slots["property"] = "permeability"
        elif "poro" in text_lower:
            slots["property"] = "porosity"
        elif "water" in text_lower and "sat" in text_lower:
            slots["property"] = "water_saturation"
        elif "oil" in text_lower and "sat" in text_lower:
            slots["property"] = "oil_saturation"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        elif "sat" in text_lower:
            slots["property"] = "water_saturation"
        
        # Layer extraction
        layer_match = re.search(r'layer\s*(\d+)', text_lower)
        if layer_match:
            slots["layer"] = int(layer_match.group(1))
        
        # Time extraction
        time_match = re.search(r'(?:day|time)\s*(\d+)', text_lower)
        if time_match:
            slots["time_days"] = int(time_match.group(1))
        
        return Intent(IntentType.VISUALIZE_PROPERTY, 0.95, slots)
    
    # Query patterns
    query_triggers = ["what", "how much", "tell me", "get"]
    if any(t in text_lower for t in query_triggers):
        if "water cut" in text_lower:
            slots["property"] = "water_cut"
        elif "oil rate" in text_lower:
            slots["property"] = "oil_rate"
        elif "gas" in text_lower and "oil" in text_lower:
            slots["property"] = "gor"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        elif "oil" in text_lower and "prod" in text_lower:
            slots["property"] = "oil_production"
        elif "pore volume" in text_lower:
            slots["property"] = "pore_volume"
        
        return Intent(IntentType.QUERY_VALUE, 0.90, slots)
    
    # Navigate
    if "go to" in text_lower or "navigate" in text_lower or "go back" in text_lower:
        if "result" in text_lower:
            slots["target"] = "results"
        elif "model" in text_lower:
            slots["target"] = "model"
        elif "back" in text_lower:
            slots["target"] = "back"
        return Intent(IntentType.NAVIGATE, 0.90, slots)
    
    return Intent(IntentType.UNKNOWN, 0.0)


def generate_response(intent: Intent) -> str:
    """Generate response based on intent."""
    responses = {
        IntentType.CANCEL: "Operation cancelled.",
        IntentType.CONFIRM: "Confirmed. Executing...",
        IntentType.HELP: "Available commands: show [property], what is [property], help, cancel, yes/no",
        IntentType.UNKNOWN: "I didn't understand that. Try 'show permeability' or 'what is water cut'.",
    }
    
    if intent.type == IntentType.VISUALIZE_PROPERTY:
        prop = intent.slots.get("property", "property")
        layer = intent.slots.get("layer")
        time = intent.slots.get("time_days")
        
        msg = f"Showing {prop}"
        if layer:
            msg += f" at layer {layer}"
        if time:
            msg += f" at day {time}"
        return msg + "."
    
    if intent.type == IntentType.QUERY_VALUE:
        prop = intent.slots.get("property", "value")
        return f"Querying {prop}..."
    
    if intent.type == IntentType.NAVIGATE:
        target = intent.slots.get("target", "view")
        return f"Navigating to {target}."
    
    return responses.get(intent.type, "Processing...")


@app.get("/")
async def index():
    """Serve the voice capture UI."""
    static_path = Path(__file__).parent / "static" / "voice_capture.html"
    if static_path.exists():
        return FileResponse(static_path)
    return JSONResponse({"message": "Voice UI not found. Use /api/voice endpoint directly."})


@app.get("/api/health")
async def health():
    """Check API health and available backends."""
    return {
        "status": "ok",
        "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic_available": bool(os.getenv("ANTHROPIC_API_KEY")),
        "backends": ["rules"] + 
                   (["whisper"] if os.getenv("OPENAI_API_KEY") else []) +
                   (["claude"] if os.getenv("ANTHROPIC_API_KEY") else [])
    }


@app.post("/api/voice")
async def process_voice(audio: UploadFile = File(...)):
    """Process uploaded audio file."""
    
    # Save uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        transcript = ""
        
        # Try Whisper if available
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                client = OpenAI()
                
                with open(tmp_path, "rb") as audio_file:
                    result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                transcript = result.text
            except Exception as e:
                transcript = f"[Whisper error: {e}]"
        else:
            transcript = "[No OPENAI_API_KEY - using demo mode]"
        
        # Parse intent (always works - rule-based)
        intent = parse_intent_rules(transcript) if transcript and not transcript.startswith("[") else Intent(IntentType.UNKNOWN, 0.0)
        
        # Generate response
        response = generate_response(intent)
        
        return {
            "transcript": transcript,
            "intent": {
                "type": intent.type.value,
                "confidence": intent.confidence,
                "slots": intent.slots
            },
            "response": response
        }
    
    finally:
        # Cleanup
        os.unlink(tmp_path)


@app.post("/api/text")
async def process_text(text: str):
    """Process text input (skip STT)."""
    intent = parse_intent_rules(text)
    response = generate_response(intent)
    
    return {
        "transcript": text,
        "intent": {
            "type": intent.type.value,
            "confidence": intent.confidence,
            "slots": intent.slots
        },
        "response": response
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
