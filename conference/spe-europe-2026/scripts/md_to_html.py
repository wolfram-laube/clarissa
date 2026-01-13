#!/usr/bin/env python3
"""Convert merged MD to HTML with proper Mermaid support."""
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
    md_path = Path("conference/spe-europe-2026/sources/wolfram/abstract-merged.md")

md_content = md_path.read_text()

# Pre-process: protect mermaid blocks from markdown processing
mermaid_blocks = []
def save_mermaid(match):
    idx = len(mermaid_blocks)
    mermaid_blocks.append(match.group(1))
    return f'MERMAID_PLACEHOLDER_{idx}'

md_content = re.sub(r'```mermaid\n(.*?)```', save_mermaid, md_content, flags=re.DOTALL)

# Convert MD to HTML using proper library
md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])
html_body = md_converter.convert(md_content)

# Restore mermaid blocks as proper divs
for idx, mermaid_code in enumerate(mermaid_blocks):
    html_body = html_body.replace(
        f'MERMAID_PLACEHOLDER_{idx}',
        f'<div class="mermaid">\n{mermaid_code}</div>'
    )

# Remove horizontal rules (---)
html_body = re.sub(r'<hr\s*/?\s*>', '', html_body)

# Full HTML document
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CLARISSA - SPE Europe 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            line-height: 1.6;
            font-size: 11pt;
            color: #333;
        }
        h1 {
            color: #003366;
            border-bottom: 2px solid #003366;
            padding-bottom: 10px;
            font-size: 18pt;
        }
        h2 {
            color: #003366;
            margin-top: 30px;
            font-size: 14pt;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }
        h3 {
            color: #0066cc;
            font-size: 12pt;
        }
        p {
            text-align: justify;
            margin-bottom: 12px;
        }
        strong {
            color: #003366;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 10pt;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px 12px;
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
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            text-align: center;
        }
        pre {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 9pt;
        }
        code {
            font-family: 'Consolas', 'Monaco', monospace;
        }
        ul, ol {
            margin-left: 20px;
        }
        li {
            margin-bottom: 5px;
        }
        @media print {
            body { margin: 0; padding: 20px; }
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
        lineColor: '#003366',
        fontSize: '14px'
    }
});
</script>
BODY_CONTENT
</body>
</html>"""

final_html = html_template.replace('BODY_CONTENT', html_body)

# Save
Path("doc-outputs").mkdir(exist_ok=True)
Path("doc-outputs/abstract-merged.html").write_text(final_html)

print(f"✅ HTML generated: {len(final_html)} chars")
print(f"   Mermaid diagrams: {len(mermaid_blocks)}")
