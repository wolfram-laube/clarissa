#!/bin/bash
# CLARISSA Timed Recorder (Linux)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../common/config.sh"

DUR=${1:-30}; OUTPUT=$(get_output_file "demo")
[[ ! "$DUR" =~ ^[0-9]+$ ]] && echo "Usage: $0 [SECONDS]" && exit 1

RES=$(xrandr 2>/dev/null | grep '\*' | head -1 | awk '{print $1}'); RES=${RES:-1920x1080}

echo "🎬 ${DUR}s $DISPLAY ($RES) → $OUTPUT"; countdown 3
ffmpeg -y -f x11grab -framerate 30 -video_size "$RES" -i "$DISPLAY" -f pulse -i default \
    -t "$DUR" -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT" 2>/dev/null
[ -f "$OUTPUT" ] && echo "✅ $OUTPUT"
