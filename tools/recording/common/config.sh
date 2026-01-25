#!/bin/bash
# CLARISSA Recording Tools - Shared Configuration

# Output directory
if [ -z "$CLARISSA_OUTPUT_DIR" ]; then
    case "$(uname -s)" in
        Darwin) CLARISSA_OUTPUT_DIR="$HOME/Movies/CLARISSA-Demos" ;;
        *)      CLARISSA_OUTPUT_DIR="$HOME/Videos/CLARISSA-Demos" ;;
    esac
fi
mkdir -p "$CLARISSA_OUTPUT_DIR"

# PiP defaults
PIP_WIDTH=${PIP_WIDTH:-320}
PIP_HEIGHT=${PIP_HEIGHT:-240}
PIP_X=${PIP_X:-20}
PIP_Y=${PIP_Y:-20}

# Generate output filename
get_output_file() {
    local prefix=${1:-demo}
    echo "$CLARISSA_OUTPUT_DIR/${prefix}-$(date +%Y%m%d-%H%M%S).mp4"
}

# Countdown
countdown() {
    echo "Recording in ${1:-3}..."
    for i in $(seq ${1:-3} -1 1); do echo "  $i..."; sleep 1; done
    echo "🔴 Recording!"
}
