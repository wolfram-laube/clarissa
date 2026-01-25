# 🎬 CLARISSA Demo Recording Tools

Cross-platform screen recording utilities for creating CLARISSA demo videos.

## Structure

```
tools/recording/
├── setup.sh              # Run this first - detects OS, configures PATH
├── record-demo.sh        # Interactive menu
├── common/
│   └── config.sh         # Shared configuration
├── macos/
│   ├── record-pip.sh     # Screen + webcam PiP
│   ├── record-timed.sh   # Timed screen recording
│   └── record-applescript.sh  # QuickTime native
└── linux/
    ├── record-pip.sh     # Screen + webcam PiP
    └── record-timed.sh   # Timed screen recording
```

## Quick Setup

```bash
# Clone repo (if not already)
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa.git ~/Projects/clarissa

# Run setup (auto-detects macOS/Linux)
~/Projects/clarissa/tools/recording/setup.sh

# Restart terminal or:
source ~/.zshrc  # or ~/.bashrc
```

## Usage

After setup, scripts are in PATH:

```bash
# Screen + Camera PiP
record-pip.sh start 60        # 60 seconds
record-pip.sh start           # Unlimited (Ctrl+C)
record-pip.sh start --no-camera
record-pip.sh devices         # List inputs

# Timed Recording (screen only)
record-timed.sh 30            # 30 seconds
record-timed.sh 120           # 2 minutes

# Interactive Menu
record-demo.sh

# macOS only: QuickTime native
record-applescript.sh start
record-applescript.sh stop
```

## Output

| Platform | Location |
|----------|----------|
| macOS | `~/Movies/CLARISSA-Demos/` |
| Linux | `~/Videos/CLARISSA-Demos/` |

## Requirements

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install ffmpeg pulseaudio-utils v4l-utils
```

**Linux (Fedora):**
```bash
sudo dnf install ffmpeg pulseaudio-utils v4l-utils
```

## Browser Alternatives

No install needed - works in Chrome/Edge:

- [Screen Recorder](https://clarissa-40cc50.gitlab.io/demos/screen-recorder.html)
- [Screen Recorder + PiP](https://clarissa-40cc50.gitlab.io/demos/screen-recorder-pip.html)

## Update

```bash
cd ~/Projects/clarissa && git pull
```

---
Part of [CLARISSA](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa)
