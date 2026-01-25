#!/bin/bash
# CLARISSA QuickTime Recorder (macOS - AppleScript)
case "${1:-help}" in
    start) osascript -e 'tell app "QuickTime Player" to activate' -e 'tell app "QuickTime Player" to new screen recording' -e 'delay 1' -e 'tell app "System Events" to key code 49'; echo "🔴 Started (click stop or: $0 stop)" ;;
    stop)  osascript -e 'tell app "System Events" to key code 49'; echo "⏹️ Stopped" ;;
    *)     echo "Usage: $0 [start|stop]" ;;
esac
