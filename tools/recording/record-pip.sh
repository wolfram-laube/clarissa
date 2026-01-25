#!/bin/bash
# CLARISSA Demo Recorder with Picture-in-Picture Camera
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
OUTPUT="$OUTPUT_DIR/demo-pip-$TIMESTAMP.mp4"

# PiP settings
PIP_WIDTH=320
PIP_HEIGHT=240
PIP_X=20
PIP_Y=20

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
    echo ""
    echo "Examples:"
    echo "  $0 start              # Record indefinitely (Ctrl+C to stop)"
    echo "  $0 start 60           # Record for 60 seconds"
    echo "  $0 start --no-camera  # Screen only"
    echo ""
    echo "Platform: $PLATFORM"
    echo "Output:   $OUTPUT_DIR"
}

list_devices_macos() {
    echo "📹 Video Devices:"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "video devices" | grep "^\[" | head -10
    echo ""
    echo "🎤 Audio Devices:"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A20 "audio devices" | grep "^\[" | head -10
}

list_devices_linux() {
    echo "📹 Video Devices:"
    ls -la /dev/video* 2>/dev/null || echo "  No video devices found"
    echo ""
    echo "🖥️ Displays:"
    echo "  $DISPLAY (current)"
    xrandr 2>/dev/null | grep " connected" || echo "  xrandr not available"
    echo ""
    echo "🎤 Audio Devices:"
    pactl list sources short 2>/dev/null || arecord -l 2>/dev/null || echo "  Audio detection failed"
}

record_macos() {
    local DURATION=$1
    local NO_CAMERA=$2
    
    # Detect devices
    SCREEN_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "capture screen" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    CAMERA_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i "facetime\|webcam\|camera" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    MIC_DEVICE=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A100 "audio devices" | grep -i "macbook\|built-in\|microphone" | head -1 | sed 's/.*\[\([0-9]*\)\].*/\1/')
    
    SCREEN_DEVICE=${SCREEN_DEVICE:-1}
    CAMERA_DEVICE=${CAMERA_DEVICE:-0}
    MIC_DEVICE=${MIC_DEVICE:-0}
    
    echo "🎬 Recording (macOS)"
    echo "   Screen: $SCREEN_DEVICE, Camera: $CAMERA_DEVICE, Mic: $MIC_DEVICE"
    echo "   Output: $OUTPUT"
    echo "   Press Ctrl+C to stop"
    echo ""
    
    if [ "$NO_CAMERA" = "true" ]; then
        ffmpeg -y \
            -f avfoundation -framerate 30 -i "$SCREEN_DEVICE:$MIC_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    else
        ffmpeg -y \
            -f avfoundation -framerate 30 -i "$SCREEN_DEVICE:$MIC_DEVICE" \
            -f avfoundation -framerate 30 -video_size ${PIP_WIDTH}x${PIP_HEIGHT} -i "$CAMERA_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -filter_complex "[1:v]format=rgba[cam];[0:v][cam]overlay=W-w-${PIP_X}:H-h-${PIP_Y}" \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    fi
}

record_linux() {
    local DURATION=$1
    local NO_CAMERA=$2
    
    # Get screen resolution
    SCREEN_RES=$(xrandr 2>/dev/null | grep '\*' | head -1 | awk '{print $1}')
    SCREEN_RES=${SCREEN_RES:-1920x1080}
    
    # Find webcam
    CAMERA_DEVICE=$(ls /dev/video* 2>/dev/null | head -1)
    
    # Find audio (PulseAudio default)
    AUDIO_DEVICE="default"
    
    echo "🎬 Recording (Linux)"
    echo "   Screen: $DISPLAY ($SCREEN_RES)"
    echo "   Camera: ${CAMERA_DEVICE:-none}"
    echo "   Output: $OUTPUT"
    echo "   Press Ctrl+C to stop"
    echo ""
    
    if [ "$NO_CAMERA" = "true" ] || [ -z "$CAMERA_DEVICE" ]; then
        ffmpeg -y \
            -f x11grab -framerate 30 -video_size "$SCREEN_RES" -i "$DISPLAY" \
            -f pulse -i "$AUDIO_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    else
        ffmpeg -y \
            -f x11grab -framerate 30 -video_size "$SCREEN_RES" -i "$DISPLAY" \
            -f v4l2 -framerate 30 -video_size ${PIP_WIDTH}x${PIP_HEIGHT} -i "$CAMERA_DEVICE" \
            -f pulse -i "$AUDIO_DEVICE" \
            ${DURATION:+-t $DURATION} \
            -filter_complex "[1:v]format=rgba[cam];[0:v][cam]overlay=W-w-${PIP_X}:H-h-${PIP_Y}" \
            -c:v libx264 -preset ultrafast -crf 23 \
            -c:a aac -b:a 128k \
            "$OUTPUT"
    fi
}

# Parse arguments
COMMAND=${1:-help}
shift 2>/dev/null || true

NO_CAMERA=false
DURATION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-camera) NO_CAMERA=true; shift ;;
        --pip-size) IFS='x' read -r PIP_WIDTH PIP_HEIGHT <<< "$2"; shift 2 ;;
        [0-9]*) DURATION=$1; shift ;;
        *) shift ;;
    esac
done

case $COMMAND in
    start)
        if [ "$PLATFORM" = "macos" ]; then
            record_macos "$DURATION" "$NO_CAMERA"
        else
            record_linux "$DURATION" "$NO_CAMERA"
        fi
        if [ -f "$OUTPUT" ]; then
            echo ""
            echo "✅ Saved: $OUTPUT"
            echo "   Size: $(du -h "$OUTPUT" | cut -f1)"
            [ "$PLATFORM" = "macos" ] && open -R "$OUTPUT"
            [ "$PLATFORM" = "linux" ] && xdg-open "$(dirname "$OUTPUT")" 2>/dev/null || true
        fi
        ;;
    devices)
        [ "$PLATFORM" = "macos" ] && list_devices_macos
        [ "$PLATFORM" = "linux" ] && list_devices_linux
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown: $COMMAND"
        show_help
        exit 1
        ;;
esac
