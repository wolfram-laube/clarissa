#!/usr/bin/env python3
"""
Robust Markdown to HTML converter for SPE abstract with Mermaid support.
"""
import re
from pathlib import Path

def convert_md_to_html(md_content: str) -> str:
    """Convert Markdown to HTML with proper Mermaid handling."""
    
    # Remove ```markdown wrapper if present (LLM artifact)
    md = re.sub(r'^```markdown\s*\n', '', md_content)
    md = re.sub(r'\n```\s*$', '', md)
    
    # Store mermaid blocks temporarily (protect from other processing)
    mermaid_blocks = []
    def store_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f'MERMAID_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```mermaid\n(.*?)```', store_mermaid, md, flags=re.DOTALL)
    
    # Store code blocks temporarily
    code_blocks = []
    def store_code(match):
        idx = len(code_blocks)
        lang = match.group(1) or ''
        code = match.group(2)
        code_blocks.append((lang, code))
        return f'CODE_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```(\w*)\n(.*?)```', store_code, md, flags=re.DOTALL)
    
    # Convert horizontal rules
    md = re.sub(r'^---+\s*$', '<hr>', md, flags=re.MULTILINE)
    
    # Convert headers (must be done before other processing)
    md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
    md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
    md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
    
    # Convert bold and italic
    md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)
    
    # Convert unordered lists
    lines = md.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # List item
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item_content = stripped[2:]
            result.append(f'  <li>{item_content}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    md = '\n'.join(result)
    
    # Convert tables
    md = convert_tables(md)
    
    # Restore code blocks
    for idx, (lang, code) in enumerate(code_blocks):
        code_escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        replacement = f'<pre><code class="language-{lang}">{code_escaped}</code></pre>'
        md = md.replace(f'CODE_PLACEHOLDER_{idx}', replacement)
    
    # Restore mermaid blocks
    for idx, mermaid_code in enumerate(mermaid_blocks):
        replacement = f'<div class="mermaid">\n{mermaid_code}</div>'
        md = md.replace(f'MERMAID_PLACEHOLDER_{idx}', replacement)
    
    # Convert paragraphs (double newlines)
    # Split by block elements and wrap text in <p>
    blocks = re.split(r'(<h[123]>.*?</h[123]>|<hr>|<ul>.*?</ul>|<div class="mermaid">.*?</div>|<pre>.*?</pre>|<table>.*?</table>)', md, flags=re.DOTALL)
    
    result_blocks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Skip if already wrapped in block element
        if block.startswith('<h') or block.startswith('<hr') or block.startswith('<ul') or \
           block.startswith('<div') or block.startswith('<pre') or block.startswith('<table'):
            result_blocks.append(block)
        else:
            # Wrap paragraphs
            paragraphs = re.split(r'\n\n+', block)
            for p in paragraphs:
                p = p.strip()
                if p:
                    result_blocks.append(f'<p>{p}</p>')
    
    return '\n\n'.join(result_blocks)


def convert_tables(md: str) -> str:
    """Convert Markdown tables to HTML."""
    lines = md.split('\n')
    result = []
    in_table = False
    is_header = True
    
    for line in lines:
        stripped = line.strip()
        
        # Detect table row
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            
            # Skip separator row
            if all(set(c) <= set('-: ') for c in cells):
                is_header = False
                continue
            
            if not in_table:
                result.append('<table>')
                in_table = True
            
            tag = 'th' if is_header else 'td'
            row = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            result.append(row)
            
            if is_header:
                is_header = False
        else:
            if in_table:
                result.append('</table>')
                in_table = False
                is_header = True
            result.append(line)
    
    if in_table:
        result.append('</table>')
    
    return '\n'.join(result)


def main():
    # HTML template with proper styling
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLARISSA - SPE Europe Energy Conference 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.8;
            font-size: 11pt;
            color: #333;
        }}
        h1 {{
            color: #003366;
            border-bottom: 3px solid #003366;
            padding-bottom: 0.5rem;
            font-size: 24pt;
        }}
        h2 {{
            color: #003366;
            margin-top: 2rem;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.3rem;
            font-size: 16pt;
        }}
        h3 {{
            color: #0066cc;
            font-size: 13pt;
        }}
        p {{
            text-align: justify;
            margin: 1em 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 2rem 0;
        }}
        pre {{
            background: #f5f5f5;
            padding: 1rem;
            overflow-x: auto;
            border-radius: 4px;
            font-size: 9pt;
        }}
        code {{
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.5rem 0;
            font-size: 10pt;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.6rem;
            text-align: left;
        }}
        th {{
            background: #003366;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .mermaid {{
            background: #f8f9fa;
            padding: 1rem;
            margin: 1.5rem 0;
            border-radius: 4px;
            text-align: center;
        }}
        ul {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        li {{
            margin: 0.5em 0;
        }}
        strong {{
            color: #003366;
        }}
        @media print {{
            body {{ font-size: 10pt; }}
            .mermaid {{ page-break-inside: avoid; }}
            h2 {{ page-break-before: auto; }}
        }}
    </style>
</head>
<body>
<script>
mermaid.initialize({{
    startOnLoad: true,
    theme: 'base',
    themeVariables: {{
        primaryColor: '#e8f0f8',
        primaryTextColor: '#003366',
        primaryBorderColor: '#003366',
        lineColor: '#003366',
        fontSize: '14px'
    }},
    flowchart: {{ useMaxWidth: true, htmlLabels: true }},
    sequence: {{ useMaxWidth: true }}
}});
</script>

{content}

</body>
</html>'''

    # Read source
    md_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
    if not md_path.exists():
        print(f"❌ Source not found: {md_path}")
        return 1
    
    md_content = md_path.read_text(encoding='utf-8')
    print(f"📖 Read {len(md_content)} chars from {md_path}")
    
    # Convert
    html_body = convert_md_to_html(md_content)
    html_full = html_template.format(content=html_body)
    
    # Save
    out_dir = Path("doc-outputs")
    out_dir.mkdir(exist_ok=True)
    
    out_path = out_dir / "abstract-merged.html"
    out_path.write_text(html_full, encoding='utf-8')
    
    print(f"✅ HTML saved: {out_path} ({len(html_full)} chars)")
    return 0


if __name__ == "__main__":
    exit(main())
