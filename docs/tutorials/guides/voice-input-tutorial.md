# Voice Input for CLARISSA

> Talk to your reservoir simulation - no keyboard required.

## Overview

CLARISSA's voice interface allows reservoir engineers to control simulations through natural speech. This tutorial covers:

1. **Basic Setup** - Getting voice input working
2. **Supported Commands** - What you can say
3. **Best Practices** - Tips for reliable recognition
4. **Troubleshooting** - Common issues and solutions

---

## Quick Start

### Option 1: Web Interface

Simply click the microphone button 🎤 in the CLARISSA interface and speak your command.

### Option 2: Jupyter Notebook

```python
from clarissa.voice import VoiceAssistant

# Initialize (requires OPENAI_API_KEY)
assistant = VoiceAssistant()

# Process a voice command
result = await assistant.process_audio("path/to/audio.wav")
print(result.response)
```

### Option 3: Try the Demo Notebook

Open the [Voice Input Showcase](../notebooks/16_Voice_Input_Showcase.ipynb) in Google Colab for an interactive demo.

---

## Supported Commands

### Visualization Commands

| Say this... | CLARISSA does... |
|-------------|------------------|
| "Show me the permeability" | Displays 3D permeability cube |
| "Show layer 3" | Cross-section at layer 3 |
| "Show saturation at day 500" | Saturation snapshot at t=500 |
| "Play the saturation animation" | Animated Sw over time |
| "Export as GIF" | Saves animation as GIF |

### Query Commands

| Say this... | CLARISSA responds... |
|-------------|----------------------|
| "What's the oil rate?" | "The oil rate is 1,250 bbl/day" |
| "What's the water cut?" | "The water cut is 35%" |
| "How much oil have we produced?" | "Cumulative oil is 2.3 MMSTB" |

### Navigation Commands

| Say this... | CLARISSA does... |
|-------------|------------------|
| "Go to results" | Navigates to results section |
| "Show sensitivity analysis" | Opens sensitivity panel |
| "Back to model" | Returns to model builder |

### Control Commands

| Say this... | Effect |
|-------------|--------|
| "Help" | Shows available commands |
| "Stop" / "Cancel" | Cancels current action |
| "Yes" / "Confirm" | Confirms pending action |
| "Undo" | Reverts last change |

---

## Tips for Best Results

### 1. Use Domain Vocabulary

CLARISSA understands reservoir engineering terms:

```
✅ "Show permeability"          (recognized)
✅ "What's the BHP?"            (recognized)  
✅ "Display Sw at layer 5"      (recognized)

❌ "Show the rocky stuff"       (unclear)
❌ "What's the bottom pressure" (use "BHP")
```

### 2. Be Specific

```
✅ "Show water saturation at day 500, layer 3"
❌ "Show me that thing from before"
```

### 3. Wait for Confirmation

For actions that modify data, CLARISSA will ask for confirmation:

```
You: "Set permeability to 200 millidarcies"
CLARISSA: "I'll set permeability to 200 mD. Confirm?"
You: "Yes"
CLARISSA: "Done. Permeability updated."
```

### 4. Speak Clearly

- Normal speaking pace works best
- Avoid background noise when possible
- The system works well even with accents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice Processing Pipeline                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   🎤 Audio ──▶ 🗣️ Whisper ──▶ 🧠 Intent ──▶ ⚡ Action      │
│      │           (STT)         Parser       Executor        │
│      │                           │              │           │
│      │                           ▼              ▼           │
│      │                      ┌─────────┐   ┌─────────┐      │
│      │                      │ Clarify │   │   Viz   │      │
│      │                      │ Dialog  │   │ Service │      │
│      │                      └─────────┘   └─────────┘      │
│      │                                                      │
│      ◀──────────────── 🔊 Response (TTS) ◀─────────────────│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "I didn't understand that"

- Rephrase using standard terminology
- Check the [supported commands](#supported-commands) list
- Say "help" for suggestions

### No response after speaking

- Check microphone permissions in browser
- Ensure stable internet connection (for cloud mode)
- Try refreshing the page

### Wrong interpretation

- Speak more slowly
- Use exact property names (e.g., "permeability" not "perm")
- If persistent, report via feedback button

### Works in browser but not in notebook

- Notebooks use file upload instead of live microphone
- Record audio externally and upload the WAV file
- See the demo notebook for examples

---

## Offline / Air-Gapped Mode

For deployments without internet access, CLARISSA can run with local models:

```python
from clarissa.voice import VoiceAssistant

# Use local Whisper model (no API key needed)
assistant = VoiceAssistant(
    mode="local",
    whisper_model="medium"  # Options: tiny, base, small, medium, large
)
```

**Requirements:**
- ~1GB disk space for Whisper medium model
- GPU recommended for real-time performance
- First run downloads the model automatically

---

## API Reference

### VoiceAssistant

```python
class VoiceAssistant:
    """Main interface for voice commands."""
    
    def __init__(
        self,
        mode: str = "cloud",           # "cloud" or "local"
        whisper_model: str = "whisper-1",
        language: str = "en"
    ):
        ...
    
    async def process_audio(
        self,
        audio_path: str
    ) -> VoiceResponse:
        """Process audio file and execute command."""
        ...
    
    async def process_text(
        self,
        text: str
    ) -> VoiceResponse:
        """Process text command (skip STT)."""
        ...
```

### VoiceResponse

```python
@dataclass
class VoiceResponse:
    success: bool
    text: str                    # Response text
    intent: str                  # Detected intent
    action_taken: Optional[str]  # What was executed
    visualization: Optional[Any] # Plotly figure if applicable
```

---

## Next Steps

- **Try the Demo**: [16_Voice_Input_Showcase.ipynb](../notebooks/16_Voice_Input_Showcase.ipynb)
- **Full Architecture**: [ADR-028](../../architecture/adr/ADR-028-voice-input-architecture.md)
- **Contribute**: [Voice Module Source](../../../src/clarissa/voice/)

---

*Part of CLARISSA - Conversational Language Agent for Reservoir Simulation*

---

## 🎬 Recording Demo Videos

Need to record a demo of the voice interface? We have macOS tools for that!

### Quick Setup

```bash
# Install recording tools
./tools/recording/setup-recording-tools.sh

# Record a 45-second demo
record-c-timed.sh 45
```

### More Options

See the [Demo Recording Tools](../../tools/recording/README.md) for:

- **AppleScript/QuickTime** - Native macOS quality
- **ffmpeg Toggle** - Flexible start/stop
- **ffmpeg Timed** - Fire & forget

Videos are saved to `~/Movies/CLARISSA-Demos/`.
