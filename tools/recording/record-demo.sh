#!/bin/bash
# CLARISSA Recording Tools - Interactive Menu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS
case "$(uname -s)" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    *)      echo "❌ Unsupported OS"; exit 1 ;;
esac

TOOLS="$SCRIPT_DIR/$PLATFORM"

echo "🎬 CLARISSA Recording Tools"
echo "==========================="
echo ""
echo "  1) Screen + Camera PiP"
echo "  2) Screen Only (timed)"
[ "$PLATFORM" = "macos" ] && echo "  3) QuickTime (AppleScript)"
echo "  d) List Devices"
echo "  o) Open Output Folder"
echo "  q) Quit"
echo ""
read -p "Choice: " choice

case $choice in
    1)
        read -p "Duration (seconds, Enter=unlimited): " dur
        "$TOOLS/record-pip.sh" start $dur
        ;;
    2)
        read -p "Duration [30]: " dur
        "$TOOLS/record-timed.sh" ${dur:-30}
        ;;
    3)
        [ "$PLATFORM" != "macos" ] && echo "macOS only" && exit 1
        echo "1) Start  2) Stop"
        read -p "> " cmd
        [ "$cmd" = "1" ] && "$TOOLS/record-applescript.sh" start
        [ "$cmd" = "2" ] && "$TOOLS/record-applescript.sh" stop
        ;;
    d) "$TOOLS/record-pip.sh" devices ;;
    o)
        [ "$PLATFORM" = "macos" ] && open "$HOME/Movies/CLARISSA-Demos"
        [ "$PLATFORM" = "linux" ] && xdg-open "$HOME/Videos/CLARISSA-Demos" 2>/dev/null
        ;;
    q) exit 0 ;;
    *) echo "Invalid" ;;
esac
