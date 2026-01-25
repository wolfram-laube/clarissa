#!/bin/bash
# CLARISSA Screen + Camera PiP Recorder (macOS)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../common/config.sh"

OUTPUT=$(get_output_file "demo-pip")

list_devices() {
    echo "📹 Video:"; ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "video devices" | grep "^\[" | head -10
    echo "🎤 Audio:"; ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "audio devices" | grep "^\[" | head -10
}

detect() {
    SCREEN=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "capture screen" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    CAMERA=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "facetime\|webcam\|camera" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    MIC=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A99 "audio devices" | grep -i "macbook\|built-in\|mic" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    SCREEN=${SCREEN:-1}; CAMERA=${CAMERA:-0}; MIC=${MIC:-0}
}

record() {
    detect
    echo "🎬 Screen:$SCREEN Camera:$CAMERA Mic:$MIC → $OUTPUT (Ctrl+C to stop)"
    if [ "$NO_CAM" = "1" ]; then
        ffmpeg -y -f avfoundation -framerate 30 -i "$SCREEN:$MIC" ${DUR:+-t $DUR} -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT"
    else
        ffmpeg -y -f avfoundation -framerate 30 -i "$SCREEN:$MIC" \
            -f avfoundation -framerate 30 -video_size ${PIP_WIDTH}x${PIP_HEIGHT} -i "$CAMERA" ${DUR:+-t $DUR} \
            -filter_complex "[1:v][0:v]overlay=W-w-${PIP_X}:H-h-${PIP_Y}" \
            -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT"
    fi
    [ -f "$OUTPUT" ] && echo "✅ $OUTPUT" && open -R "$OUTPUT"
}

CMD=${1:-help}; shift 2>/dev/null; NO_CAM=0; DUR=""
while [[ $# -gt 0 ]]; do case $1 in --no-camera) NO_CAM=1;; [0-9]*) DUR=$1;; esac; shift; done

case $CMD in
    start) record ;;
    devices) list_devices ;;
    *) echo "Usage: $0 [start|devices] [SECONDS] [--no-camera]" ;;
esac
