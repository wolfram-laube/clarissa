#!/bin/bash
# CLARISSA Timed Recorder (macOS)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../common/config.sh"

DUR=${1:-30}; OUTPUT=$(get_output_file "demo")
[[ ! "$DUR" =~ ^[0-9]+$ ]] && echo "Usage: $0 [SECONDS]" && exit 1

SCREEN=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "capture screen" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
MIC=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A99 "audio devices" | grep -i "macbook\|built-in\|mic" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
SCREEN=${SCREEN:-1}; MIC=${MIC:-0}

echo "🎬 ${DUR}s → $OUTPUT"; countdown 3
ffmpeg -y -f avfoundation -framerate 30 -i "$SCREEN:$MIC" -t "$DUR" -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT" 2>/dev/null
[ -f "$OUTPUT" ] && echo "✅ $OUTPUT" && open -R "$OUTPUT"
