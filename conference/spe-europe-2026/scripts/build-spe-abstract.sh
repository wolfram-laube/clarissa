#!/bin/bash
# build-spe-abstract.sh - Build SPE Europe 2026 abstract with Mermaid diagrams
# Run from repository root

set -e

echo "=== SPE Europe 2026 Abstract Builder ==="
echo ""

# Check dependencies
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ Missing: $1"
        echo "   Install with: $2"
        exit 1
    fi
    echo "✓ $1"
}

echo "Checking dependencies..."
check_cmd pandoc "brew install pandoc"
check_cmd mmdc "npm install -g @mermaid-js/mermaid-cli"
check_cmd python3 "brew install python"

echo ""

# Paths
CONF_DIR="conference/spe-europe-2026"
SRC_DIR="${CONF_DIR}/sources"
OUT_DIR="${CONF_DIR}/outputs"
DIAG_DIR="${OUT_DIR}/diagrams"

mkdir -p "$OUT_DIR" "$DIAG_DIR"

# Find the main markdown file
if [ -f "${SRC_DIR}/wolfram/abstract-merged.md" ]; then
    INPUT="${SRC_DIR}/wolfram/abstract-merged.md"
elif [ -f "merged-output.md" ]; then
    INPUT="merged-output.md"
else
    echo "❌ No input file found!"
    echo "   Expected: ${SRC_DIR}/wolfram/abstract-merged.md"
    exit 1
fi

echo "Input: $INPUT"
echo ""

# Step 1: Extract and render Mermaid diagrams
echo "=== Rendering Mermaid diagrams ==="

python3 << PYTHON
import re
import subprocess
from pathlib import Path

input_file = Path("$INPUT")
output_file = Path("$OUT_DIR/for-pdf.md")
diag_dir = Path("$DIAG_DIR")

content = input_file.read_text()

pattern = r'\`\`\`mermaid\n(.*?)\`\`\`'
counter = [0]

def replace_with_image(match):
    counter[0] += 1
    mermaid_code = match.group(1).strip()
    
    # Sanitize
    mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
    
    mmd_file = diag_dir / f"diagram-{counter[0]}.mmd"
    svg_file = diag_dir / f"diagram-{counter[0]}.svg"
    
    mmd_file.write_text(mermaid_code)
    
    try:
        result = subprocess.run(
            ['mmdc', '-i', str(mmd_file), '-o', str(svg_file), '-b', 'transparent', '-w', '800'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and svg_file.exists():
            print(f"  ✓ diagram-{counter[0]}.svg")
            return f'\n![Diagram {counter[0]}]({svg_file})\n'
        else:
            print(f"  ✗ diagram-{counter[0]}: {result.stderr[:100]}")
            return match.group(0)
    except Exception as e:
        print(f"  ✗ diagram-{counter[0]}: {e}")
        return match.group(0)

processed = re.sub(pattern, replace_with_image, content, flags=re.DOTALL)
output_file.write_text(processed)
print(f"\nProcessed {counter[0]} diagrams")
PYTHON

echo ""

# Step 2: Generate PDF
echo "=== Generating PDF ==="
cd "$OUT_DIR"
pandoc for-pdf.md -o abstract-merged.pdf \
    --pdf-engine=xelatex \
    -V geometry:margin=2.5cm \
    -V fontsize=11pt \
    --resource-path=".:diagrams" \
    2>/dev/null || pandoc for-pdf.md -o abstract-merged.pdf --pdf-engine=pdflatex -V geometry:margin=2.5cm

echo "✓ abstract-merged.pdf"

# Step 3: Generate HTML (with Mermaid.js)
echo ""
echo "=== Generating HTML ==="
cd - > /dev/null

# Preprocess for HTML
python3 << PYTHON
import re
from pathlib import Path

content = Path("$INPUT").read_text()
content = re.sub(r'<br\s*/?>', ' ', content)

# Convert mermaid blocks to divs
pattern = r'\`\`\`mermaid\n(.*?)\`\`\`'
content = re.sub(pattern, r'<pre class="mermaid">\n\1</pre>', content, flags=re.DOTALL)

Path("$OUT_DIR/for-html.md").write_text(content)
PYTHON

# Check if template exists
TEMPLATE="${CONF_DIR}/templates/mermaid-template.html"
if [ -f "$TEMPLATE" ]; then
    pandoc "$OUT_DIR/for-html.md" -o "$OUT_DIR/abstract-merged.html" \
        --standalone \
        --template="$TEMPLATE" \
        --metadata title="CLARISSA - SPE Europe 2026"
else
    # Inline template
    pandoc "$OUT_DIR/for-html.md" -o "$OUT_DIR/abstract-merged.html" \
        --standalone \
        --metadata title="CLARISSA - SPE Europe 2026" \
        -H <(echo '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script><script>mermaid.initialize({startOnLoad:true});</script>')
fi
echo "✓ abstract-merged.html"

# Step 4: Generate DOCX
echo ""
echo "=== Generating DOCX ==="
pandoc "$INPUT" -o "$OUT_DIR/abstract-merged.docx"
echo "✓ abstract-merged.docx"

# Summary
echo ""
echo "=== Build Complete ==="
ls -lh "$OUT_DIR"/*.pdf "$OUT_DIR"/*.html "$OUT_DIR"/*.docx 2>/dev/null

echo ""
echo "📄 PDF:  $OUT_DIR/abstract-merged.pdf"
echo "🌐 HTML: $OUT_DIR/abstract-merged.html"
echo "📝 DOCX: $OUT_DIR/abstract-merged.docx"
