# 🎤 Voice Input for CLARISSA

Voice input enables hands-free interaction with CLARISSA - speak your reservoir engineering questions naturally.

---

## Quick Start

**Try it now:** [🎤 Voice Input Demo](../demos/voice-demo.html)

1. Open the demo in Chrome/Edge
2. Enter your OpenAI API key
3. Click 🎤 or use keyboard shortcut
4. Speak your question
5. See real-time transcription

---

## Resources

| Resource | Description |
|----------|-------------|
| [Voice Demo](../demos/voice-demo.html) | Interactive browser demo |
| [Tutorial Guide](guides/voice-input-tutorial.md) | Step-by-step walkthrough |
| [Colab Notebook](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/16_Voice_Input_Showcase.ipynb) | Jupyter notebook with examples |
| [ADR-028](../architecture/decisions/adr-028-voice-input-architecture.md) | Architecture decision record |

---

## Recording Demo Videos

Need to record a demo? Multiple options:

### Browser-Based (Zero Install)

- [Screen Recorder](../demos/screen-recorder.html) - Basic recording
- [Screen Recorder + PiP](../demos/screen-recorder-pip.html) - With webcam overlay

### Command Line Tools (macOS/Linux)

```bash
# Setup (one time)
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git ~/Projects/clarissa
~/Projects/clarissa/tools/recording/setup.sh

# Use (after restart or source ~/.zshrc)
record-pip.sh start 60     # 60s with camera PiP
record-timed.sh 30         # 30s screen only
record-demo.sh             # Interactive menu
```

**Structure:**
```
tools/recording/
├── setup.sh              # Auto-detects macOS/Linux
├── common/config.sh      # Shared settings
├── macos/                # macOS-specific scripts
│   ├── record-pip.sh
│   ├── record-timed.sh
│   └── record-applescript.sh
└── linux/                # Linux-specific scripts
    ├── record-pip.sh
    └── record-timed.sh
```

📋 **Showcase Guide:** See the [Demo Showcase Guide](guides/demo-showcase-guide.md) for step-by-step instructions on what to say, demonstrate, and expect in your demo video.

See [Recording Tools Documentation](../tools/recording/README.md) for full details.

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Browser Demo | ✅ Live | WebSpeech API |
| Tutorial Guide | ✅ Complete | Step-by-step |
| Colab Notebook | ✅ Complete | With mic workaround |
| Recording Tools | ✅ Complete | macOS + Linux |
| ADR-028 | ✅ Documented | Architecture |
| Phase 1 Backend | 🔜 Planned | Issues #67-72 |

---

## Architecture

Voice input uses the WebSpeech API for browser-based transcription:

```
User Speech → Microphone → WebSpeech API → Text → CLARISSA
```

For production deployment, the architecture supports multiple backends:
- OpenAI Whisper (cloud)
- Local Whisper (privacy-focused)
- WebSpeech (browser-native)

See [ADR-028](../architecture/decisions/adr-028-voice-input-architecture.md) for details.

---

## Related Issues

- [#66 Voice Input Feature](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues/66) - Epic
- [#67-72](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues?label_name=voice-input) - Implementation tasks
