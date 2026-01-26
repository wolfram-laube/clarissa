# 🛠️ CLARISSA Tools

Developer and productivity tools for the CLARISSA project.

## Available Tools

### 🎬 [Demo Recording](recording/README.md)

Cross-platform screen recording utilities for creating demo videos.

```bash
# Quick setup
./tools/recording/setup.sh

# Usage
record-pip.sh start 60     # Screen + camera PiP
record-timed.sh 30         # Timed recording
record-demo.sh             # Interactive menu
```

**Platforms:** macOS, Linux

**Structure:**
```
recording/
├── setup.sh          # Auto-detects OS
├── common/           # Shared config
├── macos/            # macOS scripts
└── linux/            # Linux scripts
```

---

## Browser-Based Tools

No installation required - open in Chrome/Edge:

| Tool | Description |
|------|-------------|
| [Voice Demo](https://irena-40cc50.gitlab.io/demos/voice-demo.html) | Voice input demonstration |
| [Screen Recorder](https://irena-40cc50.gitlab.io/demos/screen-recorder.html) | Basic screen recording |
| [Screen Recorder + PiP](https://irena-40cc50.gitlab.io/demos/screen-recorder-pip.html) | With webcam overlay |

---

## For Team Members

**Ian, Mike, Doug:** Clone the repo and run setup:

```bash
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git ~/Projects/clarissa
~/Projects/clarissa/tools/recording/setup.sh
source ~/.zshrc
```

Then use `record-pip.sh`, `record-timed.sh`, etc. directly from terminal.
