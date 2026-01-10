#!/usr/bin/env python3
"""
preprocess_mermaid.py - Convert mermaid code blocks and fix compatibility issues

Fixes:
1. Convert ```mermaid blocks to <pre class="mermaid"> for Mermaid.js
2. Remove emojis from sequence diagram participants (cause rendering issues)
3. Replace <br/> tags with spaces in messages
"""
import re
import sys
from pathlib import Path


# Emoji pattern to remove
EMOJI_PATTERN = r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF\u2B50\u2705\u274C\u2714\u2699]+'


def fix_sequence_diagram(mermaid_code: str) -> str:
    """Fix sequence diagram syntax for better compatibility"""
    
    if 'sequenceDiagram' not in mermaid_code:
        return mermaid_code
    
    # Remove emojis from participant lines
    # Pattern: "as 👷 Field Engineer" -> "as Field Engineer"
    mermaid_code = re.sub(
        r'(as\s+)' + EMOJI_PATTERN + r'\s*',
        r'\1',
        mermaid_code
    )
    
    # Replace <br/> and <br> tags with spaces
    mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
    
    # Remove any remaining emojis in messages
    mermaid_code = re.sub(EMOJI_PATTERN, '', mermaid_code)
    
    return mermaid_code


def convert_mermaid_blocks(content: str) -> str:
    """Convert ```mermaid blocks to <pre class="mermaid"> for Mermaid.js"""
    
    # Pattern to match mermaid code blocks
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        
        # Fix sequence diagrams
        mermaid_code = fix_sequence_diagram(mermaid_code)
        
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
    
    # Check for sequence diagrams
    if 'sequenceDiagram' in content:
        print("Fixed sequence diagram compatibility issues (emojis, <br/> tags)")


if __name__ == "__main__":
    main()
