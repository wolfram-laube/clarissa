#!/bin/bash
# CLARISSA Recording Tools - Complete Installer
# Installs all tools to ~/bin/clarissa/

set -e

INSTALL_DIR="$HOME/bin/clarissa"
REPO_URL="https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git"

echo "🎬 CLARISSA Recording Tools Installer"
echo "======================================"
echo ""
echo "Installing to: $INSTALL_DIR"
echo ""

# Create directory
mkdir -p "$INSTALL_DIR"

# Clone only what we need (sparse checkout)
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "📥 Downloading tools..."
git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" clarissa 2>/dev/null
cd clarissa
git sparse-checkout set tools/recording 2>/dev/null

# Copy scripts
echo "📦 Installing scripts..."
cp tools/recording/*.sh "$INSTALL_DIR/" 2>/dev/null || true

# Make executable
chmod +x "$INSTALL_DIR"/*.sh

# Cleanup
cd /
rm -rf "$TEMP_DIR"

# Create convenient symlinks in ~/bin for direct access
mkdir -p "$HOME/bin"
for script in "$INSTALL_DIR"/*.sh; do
    name=$(basename "$script" .sh)
    ln -sf "$script" "$HOME/bin/$name" 2>/dev/null || true
done

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    [[ -f "$HOME/.bashrc" ]] && SHELL_RC="$HOME/.bashrc"
    
    if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo '# CLARISSA tools' >> "$SHELL_RC"
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_RC"
        echo "✅ Added ~/bin to PATH in $SHELL_RC"
        echo "   Run: source $SHELL_RC"
    fi
fi

# Create a handy README
cat > "$INSTALL_DIR/README.txt" << 'README'
🎬 CLARISSA Recording Tools
============================

Installed scripts:
  record-a-applescript.sh  - QuickTime recording via AppleScript
  record-b-ffmpeg.sh       - ffmpeg with start/stop toggle
  record-c-timed.sh        - ffmpeg with timer (e.g., 60 seconds)
  record-pip.sh            - Screen + webcam picture-in-picture
  record-demo.sh           - Interactive menu for all options

Quick usage:
  record-pip.sh start 60        # 60 sec with camera PiP
  record-c-timed.sh 45          # 45 sec screen only
  record-demo.sh                # Interactive menu

Output folder: ~/Movies/CLARISSA-Demos/

Browser alternatives (no install needed):
  https://irena-40cc50.gitlab.io/demos/screen-recorder.html
  https://irena-40cc50.gitlab.io/demos/screen-recorder-pip.html

Update tools:
  curl -sL https://raw.githubusercontent.com/wolfram-laube/clarissa/main/tools/recording/setup-clarissa-tools.sh | bash

README

echo ""
echo "✅ Installation complete!"
echo ""
echo "📁 Installed to: $INSTALL_DIR"
echo ""
echo "Scripts available:"
ls -1 "$INSTALL_DIR"/*.sh | while read f; do
    echo "   $(basename $f .sh)"
done
echo ""
echo "🚀 Quick start:"
echo "   record-pip.sh start 60    # Record 60s with camera"
echo "   record-c-timed.sh 30      # Record 30s screen only"
echo "   record-demo.sh            # Interactive menu"
echo ""
echo "📂 Recordings saved to: ~/Movies/CLARISSA-Demos/"
echo ""

# Open the install folder
open "$INSTALL_DIR"
