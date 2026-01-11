#!/usr/bin/env python3
"""
preprocess_mermaid.py - Convert mermaid code blocks for HTML/PDF rendering
Version 2: Better handling of quotes and special characters
"""
import re
import sys
from pathlib import Path


def sanitize_mermaid_for_html(mermaid_code: str) -> str:
    """Sanitize mermaid code for HTML rendering."""
    code = mermaid_code
    
    # Remove <br/> tags - replace with space
    code = re.sub(r'<br\s*/?>', ' ', code)
    
    # For sequence diagrams, we need to handle quotes carefully
    # Mermaid.js in HTML has trouble with unescaped quotes in messages
    
    # Check if this is a sequence diagram
    if 'sequenceDiagram' in code:
        # Replace curly quotes with straight quotes first
        code = code.replace('"', '"').replace('"', '"')
        code = code.replace(''', "'").replace(''', "'")
        
        # In sequence diagrams, messages after : should have quotes escaped
        # Pattern: A->>B: "message" or A-->>B: "message"
        # The quotes in the message text can cause issues
        
        # Option 1: Remove the outer quotes from messages (they're not required)
        # Pattern matches: ->>X: "text" or -->>X: "text"
        code = re.sub(
            r'([-]+>>[\w\s]+:\s*)"([^"]*)"',
            r'\1\2',
            code
        )
        
        # Also handle Note content with quotes
        code = re.sub(
            r'(Note\s+(?:over|left of|right of)\s+[\w,\s]+:\s*)"([^"]*)"',
            r'\1\2',
            code
        )
    
    return code.strip()


def convert_for_html(content: str) -> str:
    """Convert mermaid blocks to HTML pre tags for Mermaid.js"""
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        sanitized = sanitize_mermaid_for_html(mermaid_code)
        return f'<pre class="mermaid">\n{sanitized}\n</pre>'
    
    return re.sub(pattern, replace_block, content, flags=re.DOTALL)


def get_diagram_title(mermaid_code: str) -> str:
    """Extract a title from the mermaid code"""
    title_match = re.search(r'title\s+(.+?)$', mermaid_code, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    
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
    return "Diagram"


def convert_for_pdf(content: str) -> str:
    """Replace mermaid blocks with placeholder boxes for PDF"""
    pattern = r'```mermaid\n(.*?)```'
    diagram_count = [0]
    
    def replace_block(match):
        diagram_count[0] += 1
        mermaid_code = match.group(1).strip()
        title = get_diagram_title(mermaid_code)
        return f'\n> **[{title}]**\n> \n> *Interactive diagram available in HTML version*\n'
    
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
        count = len(re.findall(r'```mermaid', content))
        print(f"Converted {count} mermaid blocks for HTML")
    
    output_file.write_text(processed)


if __name__ == "__main__":
    main()
