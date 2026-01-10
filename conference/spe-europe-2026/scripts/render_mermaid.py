#!/usr/bin/env python3
"""
render_mermaid.py - Extract mermaid blocks, render to SVG, replace with image refs
"""
import re
import subprocess
import sys
from pathlib import Path

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'merged-output.md'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'doc-outputs'
    
    content = Path(input_file).read_text()
    
    # Find all mermaid blocks
    pattern = r'```mermaid\n(.*?)```'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    print(f"Found {len(matches)} mermaid diagrams")
    
    for i, match in enumerate(matches):
        mermaid_code = match.group(1).strip()
        # Sanitize <br/> tags
        mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
        
        # Write to temp file
        mmd_file = f'/tmp/diagram_{i}.mmd'
        svg_file = f'{output_dir}/diagram_{i}.svg'
        
        Path(mmd_file).write_text(mermaid_code)
        
        # Render with mermaid-cli
        result = subprocess.run(
            ['mmdc', '-i', mmd_file, '-o', svg_file, '-b', 'transparent', '-w', '800'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ Rendered diagram {i+1}")
        else:
            print(f"  ✗ Failed diagram {i+1}: {result.stderr[:200]}")
            # Keep original code block if rendering fails
            continue
    
    # Replace mermaid blocks with image references
    counter = [0]
    def replace_with_image(match):
        idx = counter[0]
        counter[0] += 1
        svg_path = f'{output_dir}/diagram_{idx}.svg'
        if Path(svg_path).exists():
            return f'![Architecture Diagram {idx+1}](diagram_{idx}.svg)'
        else:
            # Keep as code block if SVG doesn't exist
            return match.group(0)
    
    pdf_content = re.sub(pattern, replace_with_image, content, flags=re.DOTALL)
    Path(f'{output_dir}/for-pdf.md').write_text(pdf_content)
    print(f"Created {output_dir}/for-pdf.md with image references")

if __name__ == "__main__":
    main()
