#!/usr/bin/env python3
"""Convert merged MD to HTML with Mermaid support using proper markdown parser."""
import re
from pathlib import Path

try:
    import markdown
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "markdown", "--quiet"])
    import markdown

# Read source
md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
if not md_path.exists():
    # Fallback to existing merged file
    md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
    
md_content = md_path.read_text()

# Extract mermaid blocks before markdown processing (protect them)
mermaid_blocks = {}
counter = [0]

def save_mermaid(match):
    key = f"MERMAID_PLACEHOLDER_{counter[0]}"
    counter[0] += 1
    mermaid_blocks[key] = match.group(1)
    return key

md_content = re.sub(r'```mermaid\n(.*?)```', save_mermaid, md_content, flags=re.DOTALL)

# Convert markdown to HTML
html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'nl2br']
)

# Restore mermaid blocks as proper divs
for key, mermaid_code in mermaid_blocks.items():
    html_body = html_body.replace(
        f"<p>{key}</p>",
        f'<div class="mermaid">\n{mermaid_code}</div>'
    )
    html_body = html_body.replace(
        key,
        f'<div class="mermaid">\n{mermaid_code}</div>'
    )

# Full HTML document
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLARISSA - SPE Europe 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 850px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.8;
            font-size: 11pt;
            color: #333;
        }
        h1 {
            color: #003366;
            border-bottom: 3px solid #003366;
            padding-bottom: 0.5rem;
            font-size: 1.8rem;
        }
        h2 {
            color: #003366;
            margin-top: 2rem;
            font-size: 1.4rem;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.3rem;
        }
        h3 {
            color: #0066cc;
            font-size: 1.2rem;
        }
        p {
            margin-bottom: 1rem;
            text-align: justify;
        }
        pre {
            background: #f5f5f5;
            padding: 1rem;
            overflow-x: auto;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        code {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1.5rem 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 0.6rem;
            text-align: left;
        }
        th {
            background: #003366;
            color: white;
        }
        tr:nth-child(even) {
            background: #f9f9f9;
        }
        .mermaid {
            background: #f8f9fa;
            padding: 1rem;
            margin: 1.5rem 0;
            border-radius: 4px;
            text-align: center;
        }
        hr {
            border: none;
            border-top: 1px solid #ccc;
            margin: 2rem 0;
        }
        strong {
            color: #003366;
        }
        ul, ol {
            margin-bottom: 1rem;
            padding-left: 2rem;
        }
        li {
            margin-bottom: 0.3rem;
        }
        @media print {
            body { font-size: 10pt; }
            .mermaid { page-break-inside: avoid; }
            h2 { page-break-after: avoid; }
        }
    </style>
</head>
<body>
<script>
    mermaid.initialize({
        startOnLoad: true,
        theme: 'base',
        themeVariables: {
            primaryColor: '#e8f0f8',
            primaryTextColor: '#003366',
            primaryBorderColor: '#003366',
            fontSize: '14px'
        }
    });
</script>
"""

html_full = html_template + html_body + "\n</body>\n</html>"

# Save
Path("doc-outputs").mkdir(exist_ok=True)
Path("doc-outputs/abstract-merged.html").write_text(html_full)

print(f"✅ HTML generated: {len(html_full)} chars")
print(f"   Mermaid blocks: {len(mermaid_blocks)}")
