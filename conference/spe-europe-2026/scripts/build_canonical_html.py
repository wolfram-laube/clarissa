#!/usr/bin/env python3
"""Build HTML from canonical markdown files with Mermaid.js support.
Version 2: Fixed list handling with proper ol/ul wrappers and empty line support.
"""
import re
from pathlib import Path


def is_list_item(line: str) -> tuple[bool, bool, str]:
    """Check if line is a list item. Returns (is_list, is_ordered, content)."""
    stripped = line.strip()
    if stripped.startswith('- ') or stripped.startswith('* '):
        return True, False, stripped[2:]
    if re.match(r'^\d+\.\s+', stripped):
        return True, True, re.sub(r'^\d+\.\s+', '', stripped)
    return False, False, ''


def peek_next_list_item(lines: list[str], current_idx: int) -> tuple[bool, bool]:
    """Look ahead to find next non-empty line and check if it's a list item."""
    for i in range(current_idx + 1, len(lines)):
        line = lines[i].strip()
        if line:  # Found next non-empty line
            is_list, is_ordered, _ = is_list_item(line)
            return is_list, is_ordered
    return False, False


def md_to_html(md_content: str, title: str) -> str:
    """Convert markdown to HTML with Mermaid.js support."""
    html = md_content
    
    # Store mermaid blocks temporarily
    mermaid_blocks = []
    def store_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f'MERMAID_PLACEHOLDER_{idx}'
    
    html = re.sub(r'```mermaid\n(.*?)```', store_mermaid, html, flags=re.DOTALL)
    
    # Store code blocks temporarily
    code_blocks = []
    def store_code(match):
        idx = len(code_blocks)
        lang = match.group(1) or ''
        code = match.group(2)
        code_blocks.append((lang, code))
        return f'CODE_PLACEHOLDER_{idx}'
    
    html = re.sub(r'```(\w*)\n(.*?)```', store_code, html, flags=re.DOTALL)
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold/Italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Horizontal rules
    html = re.sub(r'^---+\s*$', '<hr>', html, flags=re.MULTILINE)
    
    # Tables
    html = convert_tables(html)
    
    # Process lists with proper wrapping
    lines = html.split('\n')
    result = []
    in_ul = False
    in_ol = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip placeholder lines
        if 'MERMAID_PLACEHOLDER' in stripped or 'CODE_PLACEHOLDER' in stripped:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
            i += 1
            continue
        
        # Skip if already HTML
        if stripped.startswith('<'):
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
            i += 1
            continue
        
        is_list, is_ordered, content = is_list_item(stripped)
        
        if is_list:
            if is_ordered:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if not in_ol:
                    result.append('<ol>')
                    in_ol = True
                result.append(f'  <li>{content}</li>')
            else:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                if not in_ul:
                    result.append('<ul>')
                    in_ul = True
                result.append(f'  <li>{content}</li>')
        elif not stripped:
            # Empty line - check if list continues
            next_is_list, next_is_ordered = peek_next_list_item(lines, i)
            
            if in_ol and next_is_list and next_is_ordered:
                pass  # Continue ordered list
            elif in_ul and next_is_list and not next_is_ordered:
                pass  # Continue unordered list
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append('')
        else:
            # Regular paragraph text
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(f'<p>{stripped}</p>')
        
        i += 1
    
    # Close any remaining lists
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    html = '\n'.join(result)
    
    # Restore code blocks
    for idx, (lang, code) in enumerate(code_blocks):
        code_escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        replacement = f'<pre><code class="language-{lang}">{code_escaped}</code></pre>'
        html = html.replace(f'CODE_PLACEHOLDER_{idx}', replacement)
    
    # Restore mermaid blocks
    for idx, mermaid_code in enumerate(mermaid_blocks):
        replacement = f'<div class="mermaid">\n{mermaid_code}</div>'
        html = html.replace(f'MERMAID_PLACEHOLDER_{idx}', replacement)
    
    # Clean up multiple blank lines
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    body {{ 
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; 
      max-width: 900px; 
      margin: 40px auto; 
      padding: 20px; 
      line-height: 1.7;
      color: #333;
      background: white;
    }}
    h1 {{ color: #1a365d; border-bottom: 2px solid #3182ce; padding-bottom: 10px; font-size: 1.8em; }}
    h2 {{ color: #2c5282; margin-top: 30px; font-size: 1.4em; }}
    h3 {{ color: #2b6cb0; font-size: 1.2em; }}
    p {{ margin: 1em 0; text-align: justify; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 30px 0; }}
    .mermaid {{ background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
    th {{ background: #1a365d; color: white; }}
    tr:nth-child(even) {{ background: #f7fafc; }}
    code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; }}
    pre {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 8px; overflow-x: auto; }}
    pre code {{ background: transparent; padding: 0; }}
    ul, ol {{ margin: 1em 0; padding-left: 2em; }}
    li {{ margin: 0.5em 0; }}
    strong {{ color: #1a365d; }}
    @media print {{
      body {{ font-size: 10pt; }}
      .mermaid {{ page-break-inside: avoid; }}
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
    primaryTextColor: '#1a365d',
    primaryBorderColor: '#3182ce',
    lineColor: '#2c5282',
    fontSize: '14px'
  }},
  flowchart: {{ useMaxWidth: true, htmlLabels: true }}
}});
</script>
{html}
</body>
</html>'''


def convert_tables(md: str) -> str:
    """Convert Markdown tables to HTML."""
    lines = md.split('\n')
    result = []
    in_table = False
    is_header = True
    
    for line in lines:
        stripped = line.strip()
        
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
    base = Path('conference/spe-europe-2026')
    canonical = base / 'canonical'
    outputs = base / 'outputs'
    outputs.mkdir(exist_ok=True)
    
    documents = [
        ('full-paper.md', 'CLARISSA - SPE Full Paper'),
        ('submission-form.md', 'CLARISSA - SPE Submission Form'),
    ]
    
    for filename, title in documents:
        src = canonical / filename
        if not src.exists():
            print(f'⚠️  {filename} not found, skipping')
            continue
        
        print(f'📄 Processing {filename}...')
        content = src.read_text(encoding='utf-8')
        html = md_to_html(content, title)
        
        out_file = outputs / filename.replace('.md', '.html')
        out_file.write_text(html, encoding='utf-8')
        print(f'   ✅ {out_file.name}')
    
    print(f'\n📁 Outputs in {outputs}:')
    for f in outputs.iterdir():
        print(f'   - {f.name}')


if __name__ == '__main__':
    main()
