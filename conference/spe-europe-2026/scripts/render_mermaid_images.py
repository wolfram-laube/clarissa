#!/usr/bin/env python3
"""
render_mermaid_images.py - Extract mermaid blocks, render to SVG, replace in markdown
"""
import re
import subprocess
import sys
from pathlib import Path


def extract_and_render_mermaid(content: str, output_dir: Path) -> str:
    """Extract mermaid blocks, render to SVG, return updated markdown with image refs"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pattern = r'```mermaid\n(.*?)```'
    
    counter = [0]  # Use list for closure mutability
    
    def replace_with_image(match):
        mermaid_code = match.group(1).strip()
        counter[0] += 1
        
        # Sanitize: remove <br/> tags
        mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
        
        # Write mermaid to temp file
        mmd_file = output_dir / f"diagram-{counter[0]}.mmd"
        svg_file = output_dir / f"diagram-{counter[0]}.svg"
        
        mmd_file.write_text(mermaid_code)
        
        # Render with mermaid-cli
        try:
            result = subprocess.run(
                ['mmdc', '-i', str(mmd_file), '-o', str(svg_file), '-b', 'transparent'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and svg_file.exists():
                print(f"  ✓ Rendered diagram-{counter[0]}.svg")
                return f'\n![Diagram {counter[0]}]({svg_file})\n'
            else:
                print(f"  ✗ Failed diagram-{counter[0]}: {result.stderr}")
                # Fallback: keep as code block
                return match.group(0)
        except Exception as e:
            print(f"  ✗ Error diagram-{counter[0]}: {e}")
            return match.group(0)
    
    updated = re.sub(pattern, replace_with_image, content, flags=re.DOTALL)
    print(f"Processed {counter[0]} mermaid diagrams")
    return updated


def main():
    if len(sys.argv) < 3:
        print("Usage: render_mermaid_images.py <input.md> <output.md> [diagram_dir]")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    diagram_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("diagrams")
    
    print(f"Rendering mermaid diagrams from {input_file}...")
    
    content = input_file.read_text()
    processed = extract_and_render_mermaid(content, diagram_dir)
    output_file.write_text(processed)
    
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    main()
