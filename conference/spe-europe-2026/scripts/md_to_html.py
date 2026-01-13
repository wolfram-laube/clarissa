#!/usr/bin/env python3
"""Convert merged MD to HTML with proper Mermaid support."""
import re
from pathlib import Path

# Read the merged markdown
md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
if not md_path.exists():
    # Fallback to existing merged file
    md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
    if not md_path.exists():
        print("ERROR: No merged markdown found!")
        exit(1)

md = md_path.read_text()

# Extract mermaid blocks first and replace with placeholders
mermaid_blocks = []
def save_mermaid(match):
    idx = len(mermaid_blocks)
    mermaid_blocks.append(match.group(1))
    return f'MERMAID_PLACEHOLDER_{idx}'

md = re.sub(r'```mermaid\n(.*?)```', save_mermaid, md, flags=re.DOTALL)

# Extract code blocks and replace with placeholders
code_blocks = []
def save_code(match):
    idx = len(code_blocks)
    lang = match.group(1) or ''
    code = match.group(2)
    code_blocks.append((lang, code))
    return f'CODE_PLACEHOLDER_{idx}'

md = re.sub(r'```(\w*)\n(.*?)```', save_code, md, flags=re.DOTALL)

# Convert markdown to HTML
lines = md.split('\n')
html_lines = []
in_list = False
in_table = False
table_header_done = False

for line in lines:
    stripped = line.strip()
    
    # Skip empty lines but preserve paragraph breaks
    if not stripped:
        if in_list:
            html_lines.append('</ul>')
            in_list = False
        if in_table:
            html_lines.append('</table>')
            in_table = False
            table_header_done = False
        html_lines.append('')
        continue
    
    # Horizontal rules
    if stripped == '---':
        html_lines.append('<hr>')
        continue
    
    # Headers
    if stripped.startswith('### '):
        html_lines.append(f'<h3>{stripped[4:]}</h3>')
        continue
    if stripped.startswith('## '):
        html_lines.append(f'<h2>{stripped[3:]}</h2>')
        continue
    if stripped.startswith('# '):
        html_lines.append(f'<h1>{stripped[2:]}</h1>')
        continue
    
    # Tables
    if '|' in stripped and stripped.startswith('|'):
        if '---' in stripped:
            continue  # Skip separator row
        cells = [c.strip() for c in stripped.split('|')[1:-1]]
        if not in_table:
            html_lines.append('<table>')
            in_table = True
            tag = 'th'
            table_header_done = False
        else:
            tag = 'td' if table_header_done else 'th'
            if tag == 'th':
                table_header_done = True
        row = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
        html_lines.append(row)
        continue
    
    # Lists
    if stripped.startswith('- ') or stripped.startswith('* '):
        if not in_list:
            html_lines.append('<ul>')
            in_list = True
        content = stripped[2:]
        # Handle inline formatting
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        html_lines.append(f'<li>{content}</li>')
        continue
    
    # Close list if we're no longer in one
    if in_list:
        html_lines.append('</ul>')
        in_list = False
    
    # Placeholders
    if stripped.startswith('MERMAID_PLACEHOLDER_'):
        idx = int(stripped.split('_')[-1])
        html_lines.append(f'<div class="mermaid">\n{mermaid_blocks[idx]}</div>')
        continue
    
    if stripped.startswith('CODE_PLACEHOLDER_'):
        idx = int(stripped.split('_')[-1])
        lang, code = code_blocks[idx]
        escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_lines.append(f'<pre><code class="{lang}">{escaped}</code></pre>')
        continue
    
    # Regular paragraph - apply inline formatting
    para = stripped
    para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
    para = re.sub(r'\*(.+?)\*', r'<em>\1</em>', para)
    para = re.sub(r'`([^`]+)`', r'<code>\1</code>', para)
    html_lines.append(f'<p>{para}</p>')

# Close any open elements
if in_list:
    html_lines.append('</ul>')
if in_table:
    html_lines.append('</table>')

# Build final HTML
html_head = '''<!DOCTYPE html>
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
            padding: 2rem; 
            line-height: 1.8; 
            font-size: 11pt;
            color: #333;
        }
        h1 { 
            color: #003366; 
            border-bottom: 3px solid #003366; 
            padding-bottom: 0.5rem;
            font-size: 18pt;
        }
        h2 { 
            color: #003366; 
            margin-top: 2rem; 
            border-bottom: 1px solid #ccc;
            font-size: 14pt;
        }
        h3 { 
            color: #0066cc; 
            font-size: 12pt;
        }
        p { 
            margin: 1em 0; 
            text-align: justify;
            word-wrap: break-word;
        }
        pre { 
            background: #f5f5f5; 
            padding: 1rem; 
            overflow-x: auto; 
            border-radius: 4px;
            font-size: 9pt;
        }
        code { 
            font-family: 'Consolas', 'Monaco', monospace; 
            background: #f0f0f0;
            padding: 0.1em 0.3em;
            border-radius: 3px;
        }
        pre code {
            background: none;
            padding: 0;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 1rem 0; 
            font-size: 10pt;
        }
        th, td { 
            border: 1px solid #ccc; 
            padding: 0.5rem; 
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
            background: #fafafa; 
            padding: 1rem; 
            margin: 1rem 0; 
            border: 1px solid #eee;
            border-radius: 4px;
        }
        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }
        li {
            margin: 0.5em 0;
        }
        hr {
            border: none;
            border-top: 1px solid #ccc;
            margin: 2rem 0;
        }
        strong {
            color: #003366;
        }
        @media print {
            body { max-width: none; }
            .mermaid { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
<script>mermaid.initialize({startOnLoad:true, theme:'neutral'});</script>
'''

html_body = '\n'.join(html_lines)
html_foot = '\n</body>\n</html>'

# Write output
Path("doc-outputs").mkdir(exist_ok=True)
Path("doc-outputs/abstract-merged.html").write_text(html_head + html_body + html_foot)

print(f"✅ HTML generated: doc-outputs/abstract-merged.html")
print(f"   Size: {len(html_head + html_body + html_foot)} bytes")
print(f"   Mermaid diagrams: {len(mermaid_blocks)}")
print(f"   Code blocks: {len(code_blocks)}")
