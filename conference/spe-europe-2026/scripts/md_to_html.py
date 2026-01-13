#!/usr/bin/env python3
"""Convert merged MD to HTML with proper Mermaid support using pandoc."""
import subprocess
import re
from pathlib import Path

# Read source
md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
if not md_path.exists():
    # Fallback to existing
    md_path = Path("conference/spe-europe-2026/sources/wolfram/abstract-merged.md")

md = md_path.read_text()
print(f"📖 Read {len(md)} chars from {md_path}")

# Extract mermaid blocks and replace with placeholders
mermaid_blocks = []
def save_mermaid(match):
    idx = len(mermaid_blocks)
    mermaid_blocks.append(match.group(1))
    return f'<div class="mermaid" id="mermaid-{idx}">MERMAID_PLACEHOLDER_{idx}</div>'

md_processed = re.sub(r'```mermaid\n(.*?)```', save_mermaid, md, flags=re.DOTALL)

# Write temp file for pandoc
Path("/tmp/input.md").write_text(md_processed)

# Convert with pandoc
result = subprocess.run([
    "pandoc", "/tmp/input.md",
    "-f", "markdown",
    "-t", "html5",
    "--standalone",
    "--metadata", "title=CLARISSA - SPE Europe 2026",
    "-o", "/tmp/output.html"
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"⚠️ Pandoc warning: {result.stderr}")

html = Path("/tmp/output.html").read_text()

# Restore mermaid blocks
for idx, block in enumerate(mermaid_blocks):
    html = html.replace(f'MERMAID_PLACEHOLDER_{idx}', block)

# Inject custom CSS and Mermaid JS
custom_head = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
    body { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        max-width: 900px; 
        margin: 0 auto; 
        padding: 2rem; 
        line-height: 1.6;
        font-size: 11pt;
        color: #333;
    }
    h1 { color: #003366; border-bottom: 3px solid #003366; padding-bottom: 0.5rem; }
    h2 { color: #003366; margin-top: 2rem; border-bottom: 1px solid #ccc; }
    h3 { color: #0066cc; }
    p { margin: 1em 0; text-align: justify; }
    pre { background: #f5f5f5; padding: 1rem; overflow-x: auto; border-radius: 4px; }
    code { font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; }
    table { border-collapse: collapse; width: 100%; margin: 1.5rem 0; }
    th, td { border: 1px solid #ddd; padding: 0.75rem; text-align: left; }
    th { background: #003366; color: white; }
    tr:nth-child(even) { background: #f9f9f9; }
    .mermaid { 
        background: #f8f9fa; 
        padding: 1rem; 
        margin: 1.5rem 0; 
        border-radius: 8px;
        text-align: center;
    }
    blockquote { border-left: 4px solid #003366; margin: 1rem 0; padding-left: 1rem; color: #555; }
    hr { border: none; border-top: 2px solid #003366; margin: 2rem 0; }
    strong { color: #003366; }
</style>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        mermaid.initialize({
            startOnLoad: true, 
            theme: 'base',
            themeVariables: {
                primaryColor: '#e8f0f8',
                primaryTextColor: '#003366',
                primaryBorderColor: '#003366',
                lineColor: '#003366',
                fontSize: '14px'
            }
        });
    });
</script>
"""

html = html.replace('</head>', custom_head + '\n</head>')

# Save
Path("doc-outputs").mkdir(exist_ok=True)
Path("doc-outputs/abstract-merged.html").write_text(html)

print(f"✅ HTML generated: {len(html)} chars")
print(f"   Mermaid diagrams: {len(mermaid_blocks)}")
