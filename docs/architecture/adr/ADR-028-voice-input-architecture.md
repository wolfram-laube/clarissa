# ADR-028: Voice Input Architecture for CLARISSA

| Status | Proposed |
|--------|----------|
| Date | 2026-01-24 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-024 (CLARISSA Core), ADR-025 (LLM Integration) |

---

## Context

CLARISSA's vision includes **voice-first field operation** - enabling reservoir engineers to interact with simulation tools from field tablets without keyboard input. This ADR defines the architecture for voice input processing, from speech capture to command execution.

### Use Cases

1. **Model Queries**: "What's the water cut at producer 1?"
2. **Visualization Control**: "Show me layer 3 at day 500"
3. **Parameter Changes**: "Set permeability to 150 millidarcies"
4. **Simulation Control**: "Run sensitivity on injection rate"
5. **Report Generation**: "Generate a summary of the last 5 runs"

### Requirements

| Requirement | Priority | Notes |
|-------------|----------|-------|
| Real-time transcription | P0 | < 2s latency |
| Domain vocabulary | P0 | "permeability", "OOIP", "BHP" |
| Noise tolerance | P1 | Field environments |
| Multi-language | P2 | English primary, German secondary |
| Offline capability | P2 | Air-gapped deployments |
| Speaker adaptation | P3 | Learn user accent |

---

## Decision

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLARISSA Voice Input Pipeline                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Audio   │───▶│   STT    │───▶│  Intent  │───▶│ Command  │───▶│Execute ││
│  │ Capture  │    │ (ASR)    │    │ Parser   │    │ Mapper   │    │        ││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘│
│       │              │               │               │               │      │
│       ▼              ▼               ▼               ▼               ▼      │
│   WebAudio      Whisper API      LLM + NER      Action Router    Simulator │
│   or Native     or Local         + Slot        + Validation     + Viz APIs │
│                                  Filling                                    │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════  │
│                           Feedback Loop                                     │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                              │
│       ┌──────────┐    ┌──────────┐    ┌──────────┐                         │
│       │Confidence│───▶│Clarify   │───▶│  TTS     │───▶ Audio Out           │
│       │ Scorer   │    │ Dialog   │    │ Response │                         │
│       └──────────┘    └──────────┘    └──────────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Audio Capture Layer

**Browser/Web:**
```javascript
// WebAudio API with noise suppression
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    sampleRate: 16000
  }
});
```

**Native (Field Tablet):**
- React Native + expo-av
- iOS/Android native audio APIs
- Hardware noise cancellation preferred

**Voice Activity Detection (VAD):**
- Silero VAD (lightweight, runs locally)
- Prevents sending silence to STT
- Wake word optional: "Hey CLARISSA"

---

### 2. Speech-to-Text (STT/ASR)

#### Option A: Cloud API (Default)

| Provider | Model | Latency | Cost | Domain Vocab |
|----------|-------|---------|------|--------------|
| **OpenAI Whisper API** | whisper-1 | ~1-2s | $0.006/min | Custom prompt |
| Google Speech-to-Text | latest_long | ~0.5s | $0.009/min | Adaptation |
| Azure Speech | Custom | ~0.5s | $0.01/min | Full custom |

**Recommendation:** OpenAI Whisper API
- Best accuracy for technical vocabulary
- Prompt engineering for domain terms
- Simple API integration

```python
# Whisper API with domain hint
response = openai.Audio.transcribe(
    model="whisper-1",
    file=audio_file,
    prompt="Reservoir simulation terms: permeability, porosity, "
           "water saturation, BHP, OOIP, waterflood, injector, producer"
)
```

#### Option B: Local/Offline (Air-Gapped)

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| Whisper tiny | 39 MB | Real-time | 70% |
| Whisper base | 74 MB | Real-time | 80% |
| Whisper small | 244 MB | ~2x real-time | 88% |
| **Whisper medium** | 769 MB | ~4x real-time | 92% |
| Whisper large-v3 | 1.5 GB | ~8x real-time | 95% |

**Recommendation:** Whisper medium for air-gapped
- Good accuracy/speed tradeoff
- Fine-tune on reservoir engineering audio corpus

```python
# Local Whisper with faster-whisper
from faster_whisper import WhisperModel

model = WhisperModel("medium", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio_path, language="en")
```

---

### 3. Intent Parser

Transform transcribed text into structured intents using LLM.

#### Intent Schema

```json
{
  "intent": "visualize_property",
  "confidence": 0.92,
  "slots": {
    "property": "water_saturation",
    "layer": 3,
    "time_days": 500,
    "view_type": "cross_section_xy"
  },
  "raw_text": "show me layer 3 at day 500"
}
```

#### Supported Intents

| Intent | Example | Slots |
|--------|---------|-------|
| `query_value` | "What's the oil rate?" | property, well?, time? |
| `visualize_property` | "Show permeability in 3D" | property, view_type, layer?, time? |
| `modify_parameter` | "Set perm to 150 mD" | parameter, value, unit? |
| `run_simulation` | "Run with 200 mD perm" | parameters[] |
| `run_sensitivity` | "Sweep injection rate" | parameter, range? |
| `export_results` | "Save as GIF" | format, filename? |
| `navigate` | "Go to sensitivity section" | target |
| `help` | "How do I change wells?" | topic? |
| `undo` | "Undo last change" | - |
| `confirm` | "Yes, run it" | - |
| `cancel` | "Cancel" / "Stop" | - |

#### LLM Prompt for Intent Parsing

```python
INTENT_PROMPT = """
You are a reservoir simulation assistant. Parse the user's voice command 
into a structured intent.

Available intents: query_value, visualize_property, modify_parameter, 
run_simulation, run_sensitivity, export_results, navigate, help, undo, 
confirm, cancel

Domain vocabulary:
- Properties: permeability (perm), porosity (poro), water saturation (Sw), 
  oil saturation (So), pressure, BHP, oil rate (FOPR), water rate (FWPR), 
  water cut (FWCT), cumulative oil (FOPT)
- Wells: producer, injector, PROD1, INJ1-4
- Units: mD (millidarcy), psi, bbl/day, m³/day

User said: "{transcription}"

Respond with JSON only:
{{"intent": "...", "confidence": 0.0-1.0, "slots": {{...}}, "clarification_needed": null}}
"""
```

---

### 4. Command Mapper

Maps intents to concrete API calls / function executions.

```python
COMMAND_MAP = {
    "visualize_property": {
        "handler": "visualization_service.show_property",
        "required_slots": ["property"],
        "optional_slots": ["layer", "time_days", "view_type"],
        "defaults": {"view_type": "3d_cube"}
    },
    "modify_parameter": {
        "handler": "deck_builder.update_parameter",
        "required_slots": ["parameter", "value"],
        "validation": "validate_parameter_range"
    },
    "run_simulation": {
        "handler": "simulation_service.run",
        "confirmation_required": True,
        "timeout": 300
    }
}
```

---

### 5. Confidence & Clarification

#### Low Confidence Handling

```python
if intent.confidence < 0.7:
    # Ask for clarification
    clarification = generate_clarification(intent)
    speak(clarification)
    # e.g., "Did you mean show permeability or porosity?"
    
elif intent.confidence < 0.9:
    # Confirm before execution
    speak(f"I'll {describe_action(intent)}. Is that correct?")
    await wait_for_confirmation()
```

#### Slot Filling Dialog

```
User: "Show me the saturation"
CLARISSA: "At which time? Current options are day 0 to 1800."
User: "Day 500"
CLARISSA: "Which layer? 1 through 5, or all layers in 3D?"
User: "Layer 3"
CLARISSA: [Shows Sw at layer 3, day 500]
```

---

### 6. Text-to-Speech (TTS) Response

| Provider | Quality | Latency | Cost |
|----------|---------|---------|------|
| **OpenAI TTS** | Excellent | ~0.5s | $0.015/1K chars |
| ElevenLabs | Best | ~0.3s | $0.30/1K chars |
| Google TTS | Good | ~0.2s | $0.004/1K chars |
| Local (Coqui) | OK | Real-time | Free |

**Recommendation:** OpenAI TTS (nova voice) for cloud, Coqui TTS for air-gapped.

---

## Implementation Phases

### Phase 1: Browser Prototype (2 weeks)
- WebAudio capture
- Whisper API integration
- Basic intent parsing (5 intents)
- Text response (no TTS yet)
- Integration with existing notebook viz

### Phase 2: Full Intent Coverage (2 weeks)
- All 11 intents
- Slot filling dialogs
- Confidence handling
- TTS responses
- Error recovery

### Phase 3: Field Optimization (2 weeks)
- Noise robustness testing
- Latency optimization
- Offline fallback (local Whisper)
- Mobile/tablet UI

### Phase 4: Air-Gapped Deployment (2 weeks)
- Local Whisper medium
- Local TTS (Coqui)
- No external API dependencies
- Performance tuning

---

## API Design

### Voice Service Endpoint

```yaml
POST /api/v1/voice/command
Content-Type: audio/wav

Response:
{
  "transcription": "show me layer 3 at day 500",
  "intent": {
    "name": "visualize_property",
    "confidence": 0.94,
    "slots": {
      "property": "water_saturation",
      "layer": 3,
      "time_days": 500
    }
  },
  "action": {
    "status": "executed",
    "result_url": "/api/v1/viz/saturation?layer=3&time=500"
  },
  "response_text": "Showing water saturation at layer 3, day 500.",
  "response_audio_url": "/api/v1/voice/tts/abc123.mp3"
}
```

### WebSocket for Streaming

```javascript
const ws = new WebSocket('wss://clarissa.example.com/voice/stream');

// Stream audio chunks
ws.send(audioChunk);

// Receive partial transcription
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  if (type === 'partial_transcript') {
    showPartialText(data.text);
  } else if (type === 'final_result') {
    executeAction(data.action);
  }
};
```

---

## Security Considerations

1. **Audio not stored**: Process in memory, discard after
2. **Transcription logs**: Optional, user consent required
3. **Command validation**: All destructive actions require confirmation
4. **Rate limiting**: Prevent abuse of STT/TTS APIs
5. **Air-gapped mode**: No data leaves local network

---

## Alternatives Considered

### 1. Browser-Native Speech Recognition
- ❌ Limited accuracy
- ❌ No custom vocabulary
- ✅ Zero latency, free
- **Rejected**: Accuracy too low for technical terms

### 2. AWS Transcribe
- ✅ Custom vocabulary
- ✅ Real-time streaming
- ❌ AWS lock-in
- ❌ More complex setup
- **Rejected**: Whisper simpler, better accuracy

### 3. Fine-tuned Local Model
- ✅ Best accuracy for domain
- ❌ Training data needed (hours of audio)
- ❌ Maintenance burden
- **Deferred**: Consider for Phase 4 if needed

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Transcription accuracy | > 95% | Word Error Rate on test set |
| Intent accuracy | > 90% | Correct intent on test set |
| End-to-end latency | < 3s | Audio end → Action start |
| User satisfaction | > 4/5 | Survey after pilot |
| Field usability | Works | Testing in noisy environment |

---

## References

1. [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
2. [faster-whisper](https://github.com/guillaumekln/faster-whisper)
3. [Silero VAD](https://github.com/snakers4/silero-vad)
4. [OpenAI TTS](https://platform.openai.com/docs/guides/text-to-speech)
5. ADR-024: CLARISSA Core System Architecture
6. CLARISSA Abstract: SPE Europe 2026

---

*Status: Proposed | Review requested from: Doug, Mike, Ian*
