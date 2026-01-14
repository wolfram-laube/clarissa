#!/usr/bin/env python3
"""
build_canonical.py - Build HTML and prepare for PDF generation from canonical sources.
Handles both submission-form.md (short abstract) and abstract.md (full paper).
"""
import re
import sys
from pathlib import Path
from datetime import datetime

def md_to_html(md_content: str, title: str, is_submission_form: bool = False) -> str:
    """Convert Markdown to styled HTML."""
    
    # Store mermaid blocks (for full paper)
    mermaid_blocks = []
    def store_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f'MERMAID_PLACEHOLDER_{idx}'
    
    md = re.sub(r'```mermaid\n(.*?)```', store_mermaid, md_content, flags=re.DOTALL)
    
    # Convert horizontal rules
    md = re.sub(r'^---+\s*$', '<hr>', md, flags=re.MULTILINE)
    
    # Convert headers
    md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
    md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
    md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
    
    # Convert bold and italic
    md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)
    
    # Convert tables
    lines = md.split('\n')
    result = []
    in_table = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Table detection
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            
            # Check if separator row
            if all(re.match(r'^-+$|^:?-+:?$', c) for c in cells):
                continue
            
            if not in_table:
                result.append('<table>')
                in_table = True
                result.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
            else:
                result.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        else:
            if in_table:
                result.append('</table>')
                in_table = False
            
            # Lists
            if stripped.startswith('- ') or stripped.startswith('* '):
                result.append(f'<li>{stripped[2:]}</li>')
            elif re.match(r'^\d+\.\s+', stripped):
                content = re.sub(r'^\d+\.\s+', '', stripped)
                result.append(f'<li>{content}</li>')
            elif stripped and not stripped.startswith('<'):
                result.append(f'<p>{stripped}</p>')
            else:
                result.append(line)
    
    if in_table:
        result.append('</table>')
    
    html_body = '\n'.join(result)
    
    # Restore mermaid blocks
    for i, mermaid in enumerate(mermaid_blocks):
        html_body = html_body.replace(
            f'MERMAID_PLACEHOLDER_{i}',
            f'<div class="mermaid">\n{mermaid}\n</div>'
        )
    
    # Wrap lists in ul/ol tags (simple approach)
    html_body = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>\n{m.group()}</ul>\n', html_body)
    
    # Style based on document type
    if is_submission_form:
        style = """
        body { font-family: 'Times New Roman', serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
        h1 { font-size: 16pt; text-align: center; margin-bottom: 5px; }
        h2 { font-size: 12pt; margin-top: 20px; border-bottom: 1px solid #333; }
        p { text-align: justify; margin: 10px 0; }
        .word-count { color: #666; font-size: 10pt; font-style: italic; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #f0f0f0; }
        hr { margin: 20px 0; }
        """
    else:
        style = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }
        h1 { color: #1a365d; }
        h2 { color: #2c5282; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
        h3 { color: #4a5568; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #e2e8f0; padding: 10px; }
        th { background: #f7fafc; }
        .mermaid { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        """
    
    mermaid_script = '' if is_submission_form else '''
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad:true, theme:'neutral'});</script>
    '''
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>{style}</style>
    {mermaid_script}
</head>
<body>
{html_body}
<footer style="margin-top:40px;padding-top:20px;border-top:1px solid #ccc;color:#666;font-size:0.9em;">
    Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
</footer>
</body>
</html>"""


def main():
    base = Path("conference/spe-europe-2026")
    output_dir = base / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Build submission form
    submission_path = base / "canonical" / "submission-form.md"
    if submission_path.exists():
        print(f"📄 Building submission-form...")
        md = submission_path.read_text()
        html = md_to_html(md, "SPE Submission Form - CLARISSA", is_submission_form=True)
        (output_dir / "submission-form.html").write_text(html)
        print(f"   ✅ outputs/submission-form.html")
    else:
        print(f"   ⚠️  {submission_path} not found")
    
    # Build full paper
    paper_path = base / "canonical" / "abstract.md"
    if paper_path.exists():
        print(f"📄 Building full-paper...")
        md = paper_path.read_text()
        html = md_to_html(md, "CLARISSA - Full Paper", is_submission_form=False)
        (output_dir / "full-paper.html").write_text(html)
        print(f"   ✅ outputs/full-paper.html")
    else:
        print(f"   ⚠️  {paper_path} not found")
    
    print(f"\n📁 Output directory: {output_dir}")
    for f in output_dir.iterdir():
        print(f"   {f.name}")


if __name__ == "__main__":
    main()
