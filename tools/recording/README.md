# 🎬 CLARISSA Demo Recording Tools

Cross-platform screen recording utilities (macOS + Linux) for creating CLARISSA demo videos.

## Quick Setup

**Clone the repo and add to PATH:**

```bash
# Clone to ~/Projects/clarissa (or wherever you prefer)
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git ~/Projects/clarissa

# Add tools to PATH (add to ~/.zshrc or ~/.bashrc)
echo 'export PATH="$HOME/Projects/clarissa/tools/recording:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Install ffmpeg
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Linux (Debian/Ubuntu)
```

**Or use the setup script:**
```bash
curl -sL https://raw.githubusercontent.com/wolfram-laube/clarissa/main/tools/recording/setup-clarissa-tools.sh | bash
```

## Available Scripts

| Script | Description | Platform |
|--------|-------------|----------|
| `record-pip.sh` | Screen + webcam picture-in-picture | macOS, Linux |
| `record-c-timed.sh` | Timed screen recording | macOS, Linux |
| `record-demo.sh` | Interactive menu | macOS, Linux |

## Usage

### Screen + Camera PiP
```bash
record-pip.sh start 60        # 60 seconds with camera overlay
record-pip.sh start           # Unlimited (Ctrl+C to stop)
record-pip.sh start --no-camera  # Screen only
record-pip.sh devices         # List available devices
```

### Timed Recording
```bash
record-c-timed.sh 30          # Record for 30 seconds
record-c-timed.sh 120         # Record for 2 minutes
```

### Interactive Menu
```bash
record-demo.sh
```

## Output Location

- **macOS:** `~/Movies/CLARISSA-Demos/`
- **Linux:** `~/Videos/CLARISSA-Demos/`

## Recording the Voice Demo

```bash
# 1. Open the demo
open "https://irena-40cc50.gitlab.io/demos/voice-demo.html"

# 2. Start recording with camera
record-pip.sh start 60

# 3. Perform demo while recording
#    - Enter API key
#    - Click examples or use microphone
#    - Show results

# 4. Video auto-saves to output folder
```

## Browser-Based Alternatives

No installation needed - works in Chrome/Edge:

- **[Screen Recorder](https://irena-40cc50.gitlab.io/demos/screen-recorder.html)** - Basic recording
- **[Screen Recorder + PiP](https://irena-40cc50.gitlab.io/demos/screen-recorder-pip.html)** - With webcam overlay

## Update Tools

```bash
cd ~/Projects/clarissa && git pull
```

## Team Notes

- **Ian, Mike, Doug:** Clone the repo and add `tools/recording` to your PATH
- Scripts auto-detect macOS vs Linux and adjust accordingly
- All recordings saved with timestamp: `demo-pip-YYYYMMDD-HHMMSS.mp4`

---

Part of [CLARISSA](https://gitlab.com/wolfram_laube/blauweiss_llc/irena) - Conversational Language Agent for Reservoir Simulation
