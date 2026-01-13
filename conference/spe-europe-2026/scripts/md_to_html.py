#!/usr/bin/env python3
"""Convert merged MD to HTML with Mermaid support."""
import re
from pathlib import Path

md = Path("conference/spe-europe-2026/merged/abstract-merged.md").read_text()

html_head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CLARISSA - SPE Europe 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.7; font-size: 16px; }
        h1 { color: #003366; border-bottom: 3px solid #003366; }
        h2 { color: #003366; margin-top: 2rem; }
        h3 { color: #0066cc; }
        pre { background: #f5f5f5; padding: 1rem; overflow-x: auto; }
        code { font-family: 'Consolas', monospace; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
        th, td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
        th { background: #003366; color: white; }
        .mermaid { background: #f8f9fa; padding: 1rem; margin: 1rem 0; }
    </style>
</head>
<body>
<script>mermaid.initialize({startOnLoad:true, theme:'base', themeVariables:{primaryColor:'#e8f0f8',primaryTextColor:'#003366',fontSize:'16px'}});</script>
"""

# Convert mermaid blocks
md = re.sub(r'```mermaid\n(.*?)```', r'<div class="mermaid">\n\1</div>', md, flags=re.DOTALL)

# Headers
md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)

# Bold/Italic
md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)

# Code blocks
md = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', md, flags=re.DOTALL)

# Paragraphs
md = re.sub(r'\n\n+', '\n</p>\n<p>\n', md)
md = '<p>\n' + md + '\n</p>'

Path("doc-outputs").mkdir(exist_ok=True)
Path("doc-outputs/abstract-merged.html").write_text(html_head + md + "\n</body></html>")

print("HTML generated: doc-outputs/abstract-merged.html")
