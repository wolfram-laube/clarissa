#!/bin/bash
# CLARISSA Timed Screen Recorder
# Cross-platform: macOS + Linux

set -e

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin) 
        OUTPUT_DIR="$HOME/Movies/CLARISSA-Demos"
        PLATFORM="macos"
        ;;
    Linux)
        OUTPUT_DIR="$HOME/Videos/CLARISSA-Demos"
        PLATFORM="linux"
        ;;
    *)
        echo "❌ Unsupported OS: $OS"
        exit 1
        ;;
esac

mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="$OUTPUT_DIR/demo-$TIMESTAMP.mp4"

DURATION=${1:-30}

if ! [[ "$DURATION" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 [SECONDS]"
    echo "  Example: $0 60    # Record for 60 seconds"
    exit 1
fi

echo "🎬 CLARISSA Timed Recorder ($PLATFORM)"
echo "   Duration: ${DURATION}s"
echo "   Output:   $OUTPUT"
echo ""
echo "Recording starts in 3..."
sleep 1; echo "2..."
sleep 1; echo "1..."
sleep 1; echo "🔴 Recording!"
echo ""

if [ "$PLATFORM" = "macos" ]; then
    # Detect devices
    SCREEN=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "capture screen" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    MIC=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A100 "audio devices" | grep -i "macbook\|built-in\|mic" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    SCREEN=${SCREEN:-1}
    MIC=${MIC:-0}
    
    ffmpeg -y \
        -f avfoundation -framerate 30 -i "$SCREEN:$MIC" \
        -t "$DURATION" \
        -c:v libx264 -preset ultrafast -crf 23 \
        -c:a aac -b:a 128k \
        "$OUTPUT" 2>/dev/null
else
    SCREEN_RES=$(xrandr 2>/dev/null | grep '\*' | head -1 | awk '{print $1}')
    SCREEN_RES=${SCREEN_RES:-1920x1080}
    
    ffmpeg -y \
        -f x11grab -framerate 30 -video_size "$SCREEN_RES" -i "$DISPLAY" \
        -f pulse -i default \
        -t "$DURATION" \
        -c:v libx264 -preset ultrafast -crf 23 \
        -c:a aac -b:a 128k \
        "$OUTPUT" 2>/dev/null
fi

if [ -f "$OUTPUT" ]; then
    echo ""
    echo "✅ Saved: $OUTPUT"
    echo "   Size: $(du -h "$OUTPUT" | cut -f1)"
    [ "$PLATFORM" = "macos" ] && open -R "$OUTPUT"
    [ "$PLATFORM" = "linux" ] && xdg-open "$(dirname "$OUTPUT")" 2>/dev/null || true
fi
