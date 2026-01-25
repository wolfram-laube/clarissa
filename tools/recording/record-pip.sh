#!/bin/bash
# CLARISSA Demo Recorder with Picture-in-Picture Camera
# Records screen + webcam overlay in bottom-right corner

OUTPUT_DIR="$HOME/Movies/CLARISSA-Demos"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="$OUTPUT_DIR/demo-pip-$TIMESTAMP.mp4"

# PiP settings (customize these)
PIP_WIDTH=320
PIP_HEIGHT=240
PIP_X=20      # Distance from right edge
PIP_Y=20      # Distance from bottom edge
PIP_BORDER=3
BORDER_COLOR="white"

# Detect devices
echo "🔍 Detecting devices..."
SCREEN_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "capture screen" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
CAMERA_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "facetime\|webcam\|camera" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
MIC_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A100 "audio devices" | grep -i "macbook\|built-in\|microphone" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')

# Fallbacks
SCREEN_DEVICE=${SCREEN_DEVICE:-1}
CAMERA_DEVICE=${CAMERA_DEVICE:-0}
MIC_DEVICE=${MIC_DEVICE:-0}

show_help() {
    echo "🎬 CLARISSA Demo Recorder with PiP Camera"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [DURATION]  Start recording (optional duration in seconds)"
    echo "  devices           List available devices"
    echo "  help              Show this help"
    echo ""
    echo "Options:"
    echo "  --no-camera       Record without camera overlay"
    echo "  --pip-size WxH    Set PiP size (default: 320x240)"
    echo "  --pip-pos X:Y     Set PiP margin from bottom-right (default: 20:20)"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Record indefinitely (Ctrl+C to stop)"
    echo "  $0 start 60           # Record for 60 seconds"
    echo "  $0 start --no-camera  # Screen only, no webcam"
    echo ""
}

list_devices() {
    echo "📹 Video Devices:"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "video devices" | grep "^\[" | head -10
    echo ""
    echo "🎤 Audio Devices:"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "audio devices" | grep "^\[" | head -10
    echo ""
    echo "Detected: Screen=$SCREEN_DEVICE, Camera=$CAMERA_DEVICE, Mic=$MIC_DEVICE"
}

record_with_pip() {
    local DURATION=$1
    local NO_CAMERA=$2
    
    echo "🎬 Starting recording..."
    echo "   Screen: Device $SCREEN_DEVICE"
    echo "   Camera: Device $CAMERA_DEVICE $([ "$NO_CAMERA" = "true" ] && echo "(disabled)")"
    echo "   Mic:    Device $MIC_DEVICE"
    echo "   Output: $OUTPUT"
    echo ""
    echo "Press Ctrl+C to stop recording"
    echo ""
    
    if [ "$NO_CAMERA" = "true" ]; then
        # Screen only
        ffmpeg -y \
            -f avfoundation -framerate 30 -i "$SCREEN_DEVICE:$MIC_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    else
        # Screen + PiP camera
        # The overlay filter places camera at bottom-right with margin
        ffmpeg -y \
            -f avfoundation -framerate 30 -i "$SCREEN_DEVICE:$MIC_DEVICE" \
            -f avfoundation -framerate 30 -video_size ${PIP_WIDTH}x${PIP_HEIGHT} -i "$CAMERA_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -filter_complex "
                [1:v]format=rgba,
                pad=w=${PIP_WIDTH}+${PIP_BORDER}*2:h=${PIP_HEIGHT}+${PIP_BORDER}*2:x=${PIP_BORDER}:y=${PIP_BORDER}:color=${BORDER_COLOR}@0.8,
                format=yuva420p[cam];
                [0:v][cam]overlay=W-w-${PIP_X}:H-h-${PIP_Y}
            " \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    fi
    
    if [ -f "$OUTPUT" ]; then
        echo ""
        echo "✅ Recording saved: $OUTPUT"
        echo "   Size: $(du -h "$OUTPUT" | cut -f1)"
        
        # Open in Finder
        open -R "$OUTPUT"
    fi
}

# Parse arguments
COMMAND=${1:-help}
shift

NO_CAMERA=false
DURATION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-camera)
            NO_CAMERA=true
            shift
            ;;
        --pip-size)
            IFS='x' read -r PIP_WIDTH PIP_HEIGHT <<< "$2"
            shift 2
            ;;
        --pip-pos)
            IFS=':' read -r PIP_X PIP_Y <<< "$2"
            shift 2
            ;;
        [0-9]*)
            DURATION=$1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

case $COMMAND in
    start)
        record_with_pip "$DURATION" "$NO_CAMERA"
        ;;
    devices)
        list_devices
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
