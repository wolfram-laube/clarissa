#!/usr/bin/env python3
"""
preprocess_mermaid.py - Convert mermaid code blocks to proper HTML divs
for client-side rendering with Mermaid.js
"""
import re
import sys
from pathlib import Path


def convert_mermaid_blocks(content: str) -> str:
    """Convert ```mermaid blocks to <pre class="mermaid"> for Mermaid.js"""
    
    # Pattern to match mermaid code blocks
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        # Use pre tag with mermaid class for Mermaid.js
        return f'<pre class="mermaid">\n{mermaid_code}\n</pre>'
    
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


if __name__ == "__main__":
    main()
