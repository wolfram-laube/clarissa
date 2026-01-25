# CLARISSA Voice Input Module

Voice-based interaction for reservoir simulation, as defined in **ADR-028**.

## Architecture

```
🎤 Audio → 🗣️ STT (Whisper) → 🧠 Intent Parser → ⚡ Execute → 🔊 Response
```

## Modules

| Module | Description |
|--------|-------------|
| `capture.py` | Audio capture with Voice Activity Detection (VAD) |
| `transcribe.py` | Speech-to-Text via Whisper API or local model |
| `intent.py` | Intent parsing with LLM support |
| `respond.py` | Response generation for user feedback |
| `execute.py` | Command execution and action routing |

## Quick Start

```python
from clarissa.voice import capture, transcribe, intent, respond, execute

# Initialize components
transcriber = transcribe.WhisperTranscriber()
parser = intent.IntentParser(llm_client=...)
responder = respond.ResponseGenerator()
executor = execute.CommandExecutor(viz_service=...)

# Process voice command
audio = await capture_audio()
text = await transcriber.transcribe(audio)
parsed = await parser.parse(text.text)
result = await executor.execute(parsed)
response = responder.success(parsed.type.value, **parsed.slots)

print(response.text)
```

## Supported Intents (Phase 1)

| Intent | Example |
|--------|---------|
| `visualize_property` | "Show me permeability in 3D" |
| `query_value` | "What is the oil rate?" |
| `navigate` | "Go to results section" |
| `help` | "How do I run simulation?" |
| `cancel` | "Stop" / "Cancel" |

## Configuration

```bash
# Required for cloud mode
export OPENAI_API_KEY=sk-...

# For air-gapped mode, install faster-whisper
pip install faster-whisper
```

## Testing

```bash
pytest tests/voice/ -v
```

## References

- [ADR-028: Voice Input Architecture](../../docs/architecture/adr/ADR-028-voice-input-architecture.md)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Silero VAD](https://github.com/snakers4/silero-vad)
