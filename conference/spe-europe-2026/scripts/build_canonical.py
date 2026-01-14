#!/usr/bin/env python3
"""
build_canonical.py - Build HTML and PDF from canonical markdown sources.
Handles both full-paper.md and submission-form.md.
"""
import re
import os
import sys
from pathlib import Path

def convert_md_to_html(md_content: str, title: str, include_mermaid_js: bool = True) -> str:
    """Convert Markdown to standalone HTML with optional Mermaid.js support."""
    
    # Store mermaid blocks
    mermaid_blocks = []
    def store_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f'MERMAID_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```mermaid\n(.*?)```', store_mermaid, md_content, flags=re.DOTALL)
    
    # Convert headers
    md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
    md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
    md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
    
    # Convert formatting
    md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)
    md = re.sub(r'^---+\s*$', '<hr>', md, flags=re.MULTILINE)
    
    # Convert lists
    lines = md.split('\n')
    result = []
    in_ul, in_ol = False, False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ol:
                result.append('</ol>')
                in_ol = False
            if not in_ul:
                result.append('<ul>')
                in_ul = True
            result.append(f'<li>{stripped[2:]}</li>')
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
            if stripped:
                result.append(f'<p>{stripped}</p>')
            else:
                result.append('')
    
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    body = '\n'.join(result)
    
    # Restore mermaid blocks
    for idx, mermaid_code in enumerate(mermaid_blocks):
        body = body.replace(
            f'<p>MERMAID_PLACEHOLDER_{idx}</p>',
            f'<div class="mermaid">\n{mermaid_code}\n</div>'
        )
    
    # Build HTML
    mermaid_script = '''
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad:true, theme:'neutral'});</script>
    ''' if include_mermaid_js and mermaid_blocks else ''
    
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
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
        strong {{ color: #1a365d; }}
        ul, ol {{ margin: 15px 0; padding-left: 30px; }}
        li {{ margin: 5px 0; }}
        @media print {{ .mermaid {{ break-inside: avoid; }} }}
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
