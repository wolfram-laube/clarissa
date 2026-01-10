#!/usr/bin/env python3
"""
render_mermaid_for_pdf.py - Extract mermaid blocks, render to SVG, replace in markdown
Requires: mermaid-cli (mmdc) to be installed
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def render_mermaid_to_svg(mermaid_code: str, output_path: Path) -> bool:
    """Render mermaid code to SVG using mmdc"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        mmd_path = f.name
    
    try:
        result = subprocess.run(
            ['mmdc', '-i', mmd_path, '-o', str(output_path), '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error rendering mermaid: {e}")
        return False
    finally:
        Path(mmd_path).unlink(missing_ok=True)


def process_markdown(input_path: Path, output_path: Path, img_dir: Path):
    """Process markdown, replacing mermaid blocks with rendered SVG images"""
    content = input_path.read_text()
    img_dir.mkdir(parents=True, exist_ok=True)
    
    pattern = r'```mermaid\n(.*?)```'
    
    counter = [0]  # Use list for closure
    
    def replace_block(match):
        mermaid_code = match.group(1).strip()
        counter[0] += 1
        svg_name = f"diagram-{counter[0]}.svg"
        svg_path = img_dir / svg_name
        
        # Sanitize <br/> tags
        mermaid_code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
        
        if render_mermaid_to_svg(mermaid_code, svg_path):
            print(f"  ✓ Rendered {svg_name}")
            return f'![Diagram {counter[0]}]({img_dir.name}/{svg_name})'
        else:
            print(f"  ✗ Failed {svg_name}, keeping as code block")
            return match.group(0)
    
    processed = re.sub(pattern, replace_block, content, flags=re.DOTALL)
    output_path.write_text(processed)
    print(f"Processed {counter[0]} diagrams")


def main():
    if len(sys.argv) < 3:
        print("Usage: render_mermaid_for_pdf.py <input.md> <output.md> [img_dir]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    img_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else output_path.parent / "diagrams"
    
    process_markdown(input_path, output_path, img_dir)


if __name__ == "__main__":
    main()
