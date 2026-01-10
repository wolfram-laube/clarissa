#!/usr/bin/env python3
"""
preprocess_mermaid.py - Convert mermaid code blocks to proper HTML divs
and sanitize content for Mermaid.js rendering
"""
import re
import sys
from pathlib import Path


def sanitize_mermaid(mermaid_code: str) -> str:
    """
    Sanitize mermaid code for proper rendering:
    - Replace <br/> with space (sequence diagram messages can't have line breaks easily)
    - Handle special characters
    """
    # Replace <br/> tags with space (in sequence diagram messages)
    mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
    
    return mermaid_code


def convert_mermaid_blocks(content: str) -> str:
    """Convert ```mermaid blocks to <pre class="mermaid"> for Mermaid.js"""
    
    # Pattern to match mermaid code blocks
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        # Sanitize the mermaid code
        sanitized = sanitize_mermaid(mermaid_code)
        # Use pre tag with mermaid class for Mermaid.js
        return f'<pre class="mermaid">\n{sanitized}\n</pre>'
    
    return re.sub(pattern, replace_block, content, flags=re.DOTALL)


def main():
    if len(sys.argv) < 2:
        print("Usage: preprocess_mermaid.py <input.md> [output.md]")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file
    
    content = input_file.read_text()
    processed = convert_mermaid_blocks(content)
    output_file.write_text(processed)
    
    # Count conversions
    original_count = len(re.findall(r'```mermaid', content))
    print(f"Converted {original_count} mermaid blocks")
    print(f"Sanitized <br/> tags for sequence diagrams")


if __name__ == "__main__":
    main()
