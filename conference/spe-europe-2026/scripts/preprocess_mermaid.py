#!/usr/bin/env python3
"""
preprocess_mermaid.py - Convert mermaid code blocks for HTML/PDF rendering
"""
import re
import sys
from pathlib import Path


def sanitize_mermaid(mermaid_code: str) -> str:
    """Sanitize mermaid code - remove <br/> tags"""
    return re.sub(r'<br\s*/?>', ' ', mermaid_code)


def get_diagram_title(mermaid_code: str) -> str:
    """Extract a title from the mermaid code"""
    # Try to find title in timeline
    title_match = re.search(r'title\s+(.+?)$', mermaid_code, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    
    # Check diagram type
    if 'flowchart' in mermaid_code:
        return "Architecture Diagram"
    elif 'sequenceDiagram' in mermaid_code:
        return "Sequence Diagram"
    elif 'timeline' in mermaid_code:
        return "Timeline Diagram"
    elif 'pie' in mermaid_code:
        return "Pie Chart"
    elif 'quadrant' in mermaid_code:
        return "Quadrant Chart"
    else:
        return "Diagram"


def convert_for_html(content: str) -> str:
    """Convert mermaid blocks to HTML pre tags for Mermaid.js"""
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        sanitized = sanitize_mermaid(mermaid_code)
        return f'<pre class="mermaid">\n{sanitized}\n</pre>'
    
    return re.sub(pattern, replace_block, content, flags=re.DOTALL)


def convert_for_pdf(content: str) -> str:
    """Replace mermaid blocks with placeholder boxes for PDF"""
    pattern = r'```mermaid\n(.*?)```'
    diagram_count = [0]  # Use list for closure
    
    def replace_block(match):
        diagram_count[0] += 1
        mermaid_code = match.group(1).strip()
        title = get_diagram_title(mermaid_code)
        
        # Create a nice placeholder
        return f'''
> **[{title}]**
> 
> *Interactive diagram available in HTML version*
'''
    
    result = re.sub(pattern, replace_block, content, flags=re.DOTALL)
    print(f"Replaced {diagram_count[0]} mermaid blocks with placeholders")
    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: preprocess_mermaid.py <input.md> <output.md> [html|pdf]")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else 'html'
    
    content = input_file.read_text()
    
    if mode == 'pdf':
        processed = convert_for_pdf(content)
    else:
        processed = convert_for_html(content)
        original_count = len(re.findall(r'```mermaid', content))
        print(f"Converted {original_count} mermaid blocks for HTML")
    
    output_file.write_text(processed)


if __name__ == "__main__":
    main()
