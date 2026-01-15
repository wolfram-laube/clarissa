#!/usr/bin/env python3
"""
build_canonical.py - Build HTML and PDF from canonical markdown sources.
Handles both full-paper.md and submission-form.md.
"""
import re
import os
import sys
from pathlib import Path


def is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator row like |---|---|"""
    cells = [c.strip() for c in line.split('|')[1:-1]]
    for cell in cells:
        # Separator cells contain only dashes, colons, and spaces
        if not re.match(r'^[\-:]+$', cell):
            return False
    return len(cells) > 0


def convert_markdown_table(lines: list) -> str:
    """Convert markdown table lines to HTML table."""
    if len(lines) < 2:
        return '\n'.join(lines)
    
    html = ['<table>']
    header_done = False
    
    for i, line in enumerate(lines):
        # Skip separator row
        if is_separator_row(line):
            continue
        
        cells = [c.strip() for c in line.split('|')[1:-1]]
        
        if not header_done:
            # Header row
            html.append('  <thead><tr>')
            for cell in cells:
                cell = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                html.append(f'    <th>{cell}</th>')
            html.append('  </tr></thead>')
            html.append('  <tbody>')
            header_done = True
        else:
            # Data row
            html.append('  <tr>')
            for cell in cells:
                cell = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                html.append(f'    <td>{cell}</td>')
            html.append('  </tr>')
    
    html.append('  </tbody>')
    html.append('</table>')
    return '\n'.join(html)


def convert_md_to_html(md_content: str, title: str, include_mermaid_js: bool = True) -> str:
    """Convert Markdown to standalone HTML with optional Mermaid.js support."""
    
    # Store mermaid blocks
    mermaid_blocks = []
    def store_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f'MERMAID_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```mermaid\n(.*?)```', store_mermaid, md_content, flags=re.DOTALL)
    
    # Store code blocks
    code_blocks = []
    def store_code(match):
        idx = len(code_blocks)
        lang = match.group(1) or ''
        code = match.group(2)
        code_blocks.append((lang, code))
        return f'CODE_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```(\w*)\n(.*?)```', store_code, md, flags=re.DOTALL)
    
    # Convert headers
    md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
    md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
    md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
    
    # Convert formatting
    md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)
    md = re.sub(r'^---+\s*$', '<hr>', md, flags=re.MULTILINE)
    
    # Process tables and lists
    lines = md.split('\n')
    result = []
    in_ul, in_ol = False, False
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect table rows
        if stripped.startswith('|') and stripped.endswith('|'):
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            # End of table
            result.append(convert_markdown_table(table_lines))
            table_lines = []
            in_table = False
        
        # Handle lists
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ol:
                result.append('</ol>')
                in_ol = False
            if not in_ul:
                result.append('<ul>')
                in_ul = True
            content = stripped[2:]
            result.append(f'<li>{content}</li>')
        elif re.match(r'^\d+\.\s+', stripped):
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if not in_ol:
                result.append('<ol>')
                in_ol = True
            item = re.sub(r'^\d+\.\s+', '', stripped)
            result.append(f'<li>{item}</li>')
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            if stripped and not stripped.startswith('<'):
                result.append(f'<p>{stripped}</p>')
            else:
                result.append(line)
    
    # Close any open lists/tables
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    if in_table and table_lines:
        result.append(convert_markdown_table(table_lines))
    
    body = '\n'.join(result)
    
    # Restore mermaid blocks
    for idx, mermaid_code in enumerate(mermaid_blocks):
        body = body.replace(
            f'<p>MERMAID_PLACEHOLDER_{idx}</p>',
            f'<div class="mermaid">\n{mermaid_code}\n</div>'
        )
    
    # Restore code blocks
    for idx, (lang, code) in enumerate(code_blocks):
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        body = body.replace(
            f'<p>CODE_PLACEHOLDER_{idx}</p>',
            f'<pre><code class="{lang}">{escaped_code}</code></pre>'
        )
    
    # Build HTML with FIXED Mermaid initialization
    mermaid_script = '''
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
    mermaid.initialize({
        startOnLoad: true,
        theme: 'base',
        themeVariables: {
            fontSize: '14px',
            fontFamily: 'Georgia, serif',
            clusterBkg: '#f8f9fa',
            clusterBorder: '#888888',
            primaryTextColor: '#333333',
            secondaryTextColor: '#333333',
            tertiaryTextColor: '#333333',
            primaryBorderColor: '#666666',
            lineColor: '#666666',
            textColor: '#333333',
            mainBkg: '#ffffff',
            nodeBorder: '#666666',
            edgeLabelBackground: '#ffffff'
        },
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
        }
    });
    </script>
    ''' if include_mermaid_js and mermaid_blocks else ''
    
    css_svg_fix = '''
        .mermaid svg text,
        .mermaid svg .label,
        .mermaid svg .nodeLabel,
        .mermaid svg .cluster-label text,
        .mermaid svg span {
            fill: #333 !important;
            color: #333 !important;
        }
        .mermaid svg .cluster rect {
            stroke: #888 !important;
        }
    ''' if mermaid_blocks else ''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Georgia', serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #1a365d; border-bottom: 2px solid #1a365d; padding-bottom: 10px; }}
        h2 {{ color: #2c5282; margin-top: 30px; }}
        h3 {{ color: #3182ce; }}
        hr {{ border: none; border-top: 1px solid #ccc; margin: 30px 0; }}
        .mermaid {{ background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; }}
        th {{ background: #f0f5fa; color: #1a365d; font-weight: bold; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        strong {{ color: #1a365d; }}
        ul, ol {{ margin: 15px 0; padding-left: 30px; }}
        li {{ margin: 5px 0; }}
        pre {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 6px; overflow-x: auto; }}
        code {{ font-family: 'Consolas', monospace; }}
        @media print {{ 
            .mermaid {{ break-inside: avoid; }} 
            table {{ break-inside: avoid; }}
        }}
        {css_svg_fix}
    </style>
    {mermaid_script}
</head>
<body>
{body}
</body>
</html>'''


def main():
    base = Path("conference/spe-europe-2026")
    canonical = base / "canonical"
    outputs = base / "outputs"
    outputs.mkdir(exist_ok=True)
    
    documents = [
        ("full-paper.md", "CLARISSA - Full Paper"),
        ("submission-form.md", "CLARISSA - SPE Submission Form"),
    ]
    
    for filename, title in documents:
        src = canonical / filename
        if not src.exists():
            print(f"⚠️  {filename} not found, skipping")
            continue
            
        print(f"📄 Processing {filename}...")
        md_content = src.read_text(encoding='utf-8')
        
        # Generate HTML
        html_content = convert_md_to_html(md_content, title)
        html_out = outputs / filename.replace('.md', '.html')
        html_out.write_text(html_content, encoding='utf-8')
        print(f"   ✅ {html_out.name}")
    
    print(f"\n📁 Outputs in {outputs}:")
    for f in outputs.iterdir():
        print(f"   - {f.name}")


if __name__ == "__main__":
    main()
