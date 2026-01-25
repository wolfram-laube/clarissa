# 🎬 CLARISSA Demo Recording Tools

Screen recording utilities for creating CLARISSA demo videos on macOS.

## Quick Install

**Option 1: Download & Run (Recommended)**

1. Download the script: [setup-recording-tools.sh](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/blob/main/tools/recording/setup-recording-tools.sh?ref_type=heads)
2. Run it:
```bash
chmod +x ~/Downloads/setup-recording-tools.sh
~/Downloads/setup-recording-tools.sh
```

**Option 2: Clone & Run**
```bash
git clone --depth 1 https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git /tmp/clarissa
bash /tmp/clarissa/tools/recording/setup-recording-tools.sh
rm -rf /tmp/clarissa
```

**Option 3: From Project Root (if you have the repo)**
```bash
./tools/recording/setup-recording-tools.sh
```

## Three Recording Methods

| Method | Best For | Requires |
|--------|----------|----------|
| **A: AppleScript** | One-off recordings, precise control | macOS only |
| **B: ffmpeg Toggle** | Flexible start/stop workflow | ffmpeg |
| **C: ffmpeg Timed** | Quick demos, fire & forget | ffmpeg |

## Usage

After installation, scripts are in `~/bin/`:

```bash
# Option A: QuickTime/AppleScript
record-a-applescript.sh start
record-a-applescript.sh stop

# Option B: ffmpeg with toggle
record-b-ffmpeg.sh start
record-b-ffmpeg.sh stop
record-b-ffmpeg.sh toggle   # Start or stop
record-b-ffmpeg.sh status   # Check if recording

# Option C: Timed recording
record-c-timed.sh 30        # Record 30 seconds
record-c-timed.sh 120       # Record 2 minutes

# Interactive wrapper
record-demo.sh              # Choose method interactively
```

## Recording the Voice Demo

```bash
# 1. Open the demo
open "https://irena-40cc50.gitlab.io/demos/voice-demo.html"

# 2. Start recording (e.g., 45 seconds)
record-c-timed.sh 45

# 3. Perform demo actions while recording
#    - Enter API key
#    - Click example buttons or use microphone
#    - Show visualizations

# 4. Video auto-saves to ~/Movies/CLARISSA-Demos/
```

## Browser-Based Alternative

Don't want to install anything? Use the [🎬 Screen Recorder](../demos/screen-recorder.html) - works directly in Chrome/Edge!

## Prerequisites

For Options B & C:
```bash
brew install ffmpeg
```

## Output

All recordings are saved to:
```
~/Movies/CLARISSA-Demos/demo-YYYYMMDD-HHMMSS.mp4
```

## Tips

- **Mikrofon**: Option A requires manual selection in QuickTime. Options B & C use default mic.
- **System Audio**: To capture browser sounds, install [BlackHole](https://github.com/ExistentialAudio/BlackHole)
- **Cursor**: Options B & C capture cursor movement automatically

## Troubleshooting

**ffmpeg not found:**
```bash
brew install ffmpeg
```

**Permission denied (microphone):**
- System Preferences → Security & Privacy → Privacy → Microphone
- Enable for Terminal/iTerm

**No video output:**
```bash
# List available devices
record-b-ffmpeg.sh devices
```

---

Part of [CLARISSA](https://gitlab.com/wolfram_laube/blauweiss_llc/irena) - Conversational Language Agent for Reservoir Simulation
