#!/usr/bin/env python3
"""Build HTML from canonical markdown files with Mermaid.js support."""
import re
from pathlib import Path

def md_to_html(md_content: str, title: str) -> str:
    """Convert markdown to HTML with Mermaid.js support."""
    html = md_content
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold/Italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Horizontal rules
    html = re.sub(r'^---+\s*$', '<hr>', html, flags=re.MULTILINE)
    
    # Mermaid blocks
    html = re.sub(
        r'```mermaid\n(.*?)```',
        r'<div class="mermaid">\1</div>',
        html, flags=re.DOTALL
    )
    
    # Code blocks
    html = re.sub(
        r'```(\w*)\n(.*?)```',
        r'<pre><code class="\1">\2</code></pre>',
        html, flags=re.DOTALL
    )
    
    # Process lists
    lines = html.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('<'):
            if stripped.startswith('- '):
                result.append(f'<li>{stripped[2:]}</li>')
            elif re.match(r'^\d+\.\s', stripped):
                # Extract content after number
                content = re.sub(r'^\d+\.\s+', '', stripped)
                result.append(f'<li>{content}</li>')
            else:
                result.append(f'<p>{stripped}</p>')
        else:
            result.append(line)
    html = '\n'.join(result)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
           max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
    h1 {{ color: #1a365d; border-bottom: 2px solid #3182ce; padding-bottom: 10px; }}
    h2 {{ color: #2c5282; margin-top: 30px; }}
    h3 {{ color: #2b6cb0; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 30px 0; }}
    .mermaid {{ background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
    th {{ background: #edf2f7; }}
    code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; }}
    pre {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 8px; overflow-x: auto; }}
    li {{ margin: 5px 0; }}
  </style>
</head>
<body>
{html}
<script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
</body>
</html>'''


def main():
    base = Path('conference/spe-europe-2026/canonical')
    out = Path('doc-outputs/spe-submission')
    out.mkdir(parents=True, exist_ok=True)
    
    # Process submission form
    submission = base / 'submission-form.md'
    if submission.exists():
        content = submission.read_text()
        html = md_to_html(content, 'CLARISSA - SPE Submission Abstract')
        (out / 'submission-form.html').write_text(html)
        print('✅ Generated submission-form.html')
    else:
        print(f'⚠️ {submission} not found')
    
    # Process full paper if exists
    fullpaper = base / 'full-paper.md'
    if fullpaper.exists():
        content = fullpaper.read_text()
        html = md_to_html(content, 'CLARISSA - SPE Full Paper')
        (out / 'full-paper.html').write_text(html)
        print('✅ Generated full-paper.html')


if __name__ == '__main__':
    main()
