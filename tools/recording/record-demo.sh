#!/bin/bash
# CLARISSA Recording Tools - Interactive Menu
# Cross-platform: macOS + Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎬 CLARISSA Demo Recording Tools"
echo "================================="
echo ""
echo "Choose recording method:"
echo ""
echo "  1) Screen + Camera PiP    (picture-in-picture webcam)"
echo "  2) Screen Only (timed)    (specify duration)"
echo "  3) Screen Only (toggle)   (start/stop manually)"
echo "  4) List Devices           (show available inputs)"
echo "  5) Open Output Folder     (view recordings)"
echo ""
echo "  q) Quit"
echo ""

read -p "Selection [1-5, q]: " choice

case $choice in
    1)
        read -p "Duration in seconds (or Enter for unlimited): " duration
        if [ -n "$duration" ]; then
            "$SCRIPT_DIR/record-pip.sh" start "$duration"
        else
            "$SCRIPT_DIR/record-pip.sh" start
        fi
        ;;
    2)
        read -p "Duration in seconds [30]: " duration
        duration=${duration:-30}
        "$SCRIPT_DIR/record-c-timed.sh" "$duration"
        ;;
    3)
        echo "Starting... press Enter to stop"
        "$SCRIPT_DIR/record-pip.sh" start --no-camera &
        PID=$!
        read
        kill $PID 2>/dev/null
        ;;
    4)
        "$SCRIPT_DIR/record-pip.sh" devices
        ;;
    5)
        OS="$(uname -s)"
        if [ "$OS" = "Darwin" ]; then
            open "$HOME/Movies/CLARISSA-Demos"
        else
            xdg-open "$HOME/Videos/CLARISSA-Demos" 2>/dev/null || ls -la "$HOME/Videos/CLARISSA-Demos"
        fi
        ;;
    q|Q)
        echo "Bye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
