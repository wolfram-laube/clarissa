#!/bin/bash
# CLARISSA Screen + Camera PiP Recorder (Linux)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../common/config.sh"

OUTPUT=$(get_output_file "demo-pip")

list_devices() {
    echo "📹 Video:"; ls /dev/video* 2>/dev/null || echo "  none"; v4l2-ctl --list-devices 2>/dev/null || true
    echo "🖥️ Display: $DISPLAY"; xrandr 2>/dev/null | grep " connected" || true
    echo "🎤 Audio:"; pactl list sources short 2>/dev/null || arecord -l 2>/dev/null || echo "  none"
}

record() {
    RES=$(xrandr 2>/dev/null | grep '\*' | head -1 | awk '{print $1}'); RES=${RES:-1920x1080}
    CAM=$(ls /dev/video* 2>/dev/null | head -1)
    echo "🎬 $DISPLAY ($RES) Camera:${CAM:-none} → $OUTPUT (Ctrl+C to stop)"
    
    if [ "$NO_CAM" = "1" ] || [ -z "$CAM" ]; then
        ffmpeg -y -f x11grab -framerate 30 -video_size "$RES" -i "$DISPLAY" \
            -f pulse -i default ${DUR:+-t $DUR} \
            -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT"
    else
        ffmpeg -y -f x11grab -framerate 30 -video_size "$RES" -i "$DISPLAY" \
            -f v4l2 -framerate 30 -video_size ${PIP_WIDTH}x${PIP_HEIGHT} -i "$CAM" \
            -f pulse -i default ${DUR:+-t $DUR} \
            -filter_complex "[1:v][0:v]overlay=W-w-${PIP_X}:H-h-${PIP_Y}" \
            -c:v libx264 -preset ultrafast -crf 23 -c:a aac "$OUTPUT"
    fi
    [ -f "$OUTPUT" ] && echo "✅ $OUTPUT"
}

CMD=${1:-help}; shift 2>/dev/null; NO_CAM=0; DUR=""
while [[ $# -gt 0 ]]; do case $1 in --no-camera) NO_CAM=1;; [0-9]*) DUR=$1;; esac; shift; done

case $CMD in
    start) record ;;
    devices) list_devices ;;
    *) echo "Usage: $0 [start|devices] [SECONDS] [--no-camera]"; echo "Requires: ffmpeg, pulseaudio/pipewire" ;;
esac
