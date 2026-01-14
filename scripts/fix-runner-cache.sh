#!/bin/bash
# Fix GitLab Runner pip cache issues on macOS
# Run this when you see: "OSError: [Errno 2] No such file or directory: '__editable__.clarissa-0.1.0.pth'"

set -e

echo "🔧 Fixing GitLab Runner pip cache..."

# Remove stale editable install reference
STALE_PTH="/usr/local/Caskroom/miniconda/base/lib/python3.12/site-packages/__editable__.clarissa-0.1.0.pth"
if [ -f "$STALE_PTH" ]; then
    echo "   Removing stale .pth file..."
    rm -f "$STALE_PTH"
fi

# Also check for any other stale clarissa references
echo "   Checking for other stale clarissa references..."
find /usr/local/Caskroom/miniconda/base/lib/python3.12/site-packages -name "*clarissa*" -type f 2>/dev/null | while read f; do
    echo "   Removing: $f"
    rm -f "$f"
done

# Clear pip cache
echo "   Purging pip cache..."
pip cache purge 2>/dev/null || true

echo "✅ Done! Re-run the pipeline."
