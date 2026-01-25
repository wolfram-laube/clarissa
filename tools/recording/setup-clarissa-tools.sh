#!/bin/bash
# CLARISSA Recording Tools - Repo-Based Setup
# Clones repo and sets up PATH for all platforms (macOS/Linux)

set -e

# Default install location (can be overridden)
REPO_DIR="${CLARISSA_HOME:-$HOME/Projects/clarissa}"
REPO_URL="https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git"

echo "🎬 CLARISSA Tools Setup"
echo "======================="
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macOS" ;;
    Linux)  PLATFORM="Linux" ;;
    *)      PLATFORM="Unknown" ;;
esac
echo "Platform: $PLATFORM"

# Check if repo already exists
if [ -d "$REPO_DIR/.git" ]; then
    echo "📂 Repo exists at $REPO_DIR"
    echo "   Updating..."
    cd "$REPO_DIR"
    git pull --ff-only 2>/dev/null || echo "   (manual merge needed)"
else
    echo "📥 Cloning CLARISSA repository..."
    mkdir -p "$(dirname "$REPO_DIR")"
    git clone "$REPO_URL" "$REPO_DIR"
fi

# Make scripts executable
chmod +x "$REPO_DIR/tools/recording/"*.sh 2>/dev/null || true

# Detect shell config
if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

# Add to PATH
TOOLS_PATH="$REPO_DIR/tools/recording"
PATH_LINE="export PATH=\"$TOOLS_PATH:\$PATH\""

if ! grep -q "clarissa.*tools/recording" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# CLARISSA Recording Tools" >> "$SHELL_RC"
    echo "$PATH_LINE" >> "$SHELL_RC"
    echo "✅ Added to PATH in $SHELL_RC"
else
    echo "✅ PATH already configured"
fi

# Create output directory
mkdir -p "$HOME/Movies/CLARISSA-Demos" 2>/dev/null || mkdir -p "$HOME/Videos/CLARISSA-Demos"

# Platform-specific notes
echo ""
echo "✅ Setup complete!"
echo ""
echo "📁 Repository: $REPO_DIR"
echo "🔧 Tools:      $REPO_DIR/tools/recording/"
echo ""

if [ "$PLATFORM" = "macOS" ]; then
    echo "📦 Install ffmpeg (if not already):"
    echo "   brew install ffmpeg"
    echo ""
    OUTPUT_DIR="$HOME/Movies/CLARISSA-Demos"
elif [ "$PLATFORM" = "Linux" ]; then
    echo "📦 Install ffmpeg (if not already):"
    echo "   sudo apt install ffmpeg   # Debian/Ubuntu"
    echo "   sudo dnf install ffmpeg   # Fedora"
    echo ""
    OUTPUT_DIR="$HOME/Videos/CLARISSA-Demos"
fi

echo "🚀 Quick start (restart terminal or run: source $SHELL_RC)"
echo ""
echo "   record-pip.sh start 60     # 60s with camera PiP"
echo "   record-c-timed.sh 30       # 30s screen only"
echo "   record-demo.sh             # Interactive menu"
echo ""
echo "📂 Recordings saved to: $OUTPUT_DIR"
echo ""
echo "🔄 To update tools later:"
echo "   cd $REPO_DIR && git pull"
echo ""
