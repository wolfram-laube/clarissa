#!/bin/bash
# CLARISSA Recording Tools - Setup
# Detects OS and configures PATH

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎬 CLARISSA Recording Tools Setup"
echo "=================================="

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macos"; PLATFORM_NAME="macOS" ;;
    Linux)  PLATFORM="linux"; PLATFORM_NAME="Linux" ;;
    *)      echo "❌ Unsupported: $OS"; exit 1 ;;
esac

echo "Platform: $PLATFORM_NAME"
echo "Tools:    $SCRIPT_DIR/$PLATFORM/"

# Make executable
chmod +x "$SCRIPT_DIR/$PLATFORM/"*.sh 2>/dev/null
chmod +x "$SCRIPT_DIR/common/"*.sh 2>/dev/null

# Shell config
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

TOOLS_PATH="$SCRIPT_DIR/$PLATFORM"
PATH_EXPORT="export PATH=\"$TOOLS_PATH:\$PATH\""

if ! grep -q "clarissa.*recording.*$PLATFORM" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# CLARISSA Recording Tools ($PLATFORM_NAME)" >> "$SHELL_RC"
    echo "$PATH_EXPORT" >> "$SHELL_RC"
    echo "✅ Added to PATH in $SHELL_RC"
else
    echo "✅ PATH already configured"
fi

# Create output dir
case "$PLATFORM" in
    macos) mkdir -p "$HOME/Movies/CLARISSA-Demos" ;;
    linux) mkdir -p "$HOME/Videos/CLARISSA-Demos" ;;
esac

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo ""
    echo "⚠️  ffmpeg not found. Install it:"
    case "$PLATFORM" in
        macos) echo "   brew install ffmpeg" ;;
        linux) echo "   sudo apt install ffmpeg  # Debian/Ubuntu"
               echo "   sudo dnf install ffmpeg  # Fedora" ;;
    esac
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Available commands (restart terminal or: source $SHELL_RC):"
echo "   record-pip.sh start 60     # Screen + camera PiP"
echo "   record-timed.sh 30         # Timed screen recording"
[ "$PLATFORM" = "macos" ] && echo "   record-applescript.sh      # QuickTime native"
echo ""
echo "📂 Output: ~/$([ "$PLATFORM" = "macos" ] && echo "Movies" || echo "Videos")/CLARISSA-Demos/"
