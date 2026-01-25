# 🎤 Voice Input Feature

CLARISSA's voice input capability enables hands-free reservoir simulation control through natural language speech commands.

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [🎮 **Live Demo**](../demos/voice-demo.html) | Try it now in your browser |
| [📖 **Tutorial**](guides/voice-input-tutorial.md) | Step-by-step guide |
| [📓 **Colab Notebook**](notebooks/16_Voice_Input_Showcase.ipynb) | Interactive playground |
| [🏗️ **Architecture (ADR-028)**](../architecture/adr/ADR-028-voice-input-architecture.md) | Technical design decisions |
| [🎬 **Record a Demo**](../demos/screen-recorder.html) | Browser-based screen recorder |

---

## What Can You Do?

### Visualize Reservoir Properties
> "Show me the permeability distribution"

Generates 3D scatter plots of grid properties like porosity, permeability, and saturation.

### Explore Specific Layers
> "Show layer 3"

Creates cross-section heatmaps with well locations marked.

### Query Simulation Results
> "What is the current water cut?"

Returns calculated values from simulation output.

### Time-Based Analysis
> "Show saturation at day 500"

Visualizes property evolution over simulation time.

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Whisper   │────▶│   GPT-4o    │
│  Microphone │     │     API     │     │   Parser    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
              ┌───────────┐     ┌─────────────┐
              │  Intent   │────▶│   CLARISSA  │
              │  Router   │     │   Actions   │
              └───────────┘     └─────────────┘
```

**Pipeline:**

1. **Capture** - WebAudio API records speech
2. **Transcribe** - OpenAI Whisper converts to text
3. **Parse** - GPT-4o extracts intent & slots
4. **Execute** - CLARISSA performs visualization/query
5. **Display** - Plotly renders results

---

## Getting Started

### Option 1: Browser Demo (Quickest)

1. Open the [Voice Demo](../demos/voice-demo.html)
2. Enter your OpenAI API key
3. Click 🎤 and speak a command
4. See the visualization!

### Option 2: Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wolfram-laube/clarissa/blob/main/docs/tutorials/notebooks/16_Voice_Input_Showcase.ipynb)

The notebook includes a working microphone implementation that bypasses Colab's iframe restrictions.

### Option 3: Local Development

```bash
# Clone the repo
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
cd irena

# See the tutorial for setup
cat docs/tutorials/guides/voice-input-tutorial.md
```

---

## Recording Demo Videos

Need to record a demo? Two options:

### Browser-Based (Zero Setup)
Open the [Screen Recorder](../demos/screen-recorder.html) - works in Chrome/Edge.

### macOS Tools (More Control)
```bash
./tools/recording/setup-recording-tools.sh
record-c-timed.sh 45  # 45 second recording
```

See [Demo Recording Tools](../tools/recording/README.md) for details.

---

## Implementation Status

| Component | Status | Issue |
|-----------|--------|-------|
| Voice Capture (Browser) | ✅ Complete | - |
| Whisper Integration | ✅ Complete | - |
| Intent Parsing | ✅ Complete | - |
| 3D Visualization | ✅ Complete | - |
| Cross-Section Views | ✅ Complete | - |
| Colab Support | ✅ Complete | - |
| OPM Flow Integration | 🔜 Planned | [#68](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/68) |
| Portal Integration | 🔜 Planned | [#77](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/77) |

---

## Related Documentation

- [ADR-028: Voice Input Architecture](../architecture/adr/ADR-028-voice-input-architecture.md)
- [ADR-024: CLARISSA Core Architecture](../architecture/adr/ADR-024-clarissa-core-system-architecture.md)
- [SPE Europe 2026 Paper](../publications/spe-europe-2026/index.md)

---

## Feedback

Found a bug? Have a feature request?

- 👎 Use the thumbs down in Claude to report issues
- 📝 Open an [issue on GitLab](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/new)
