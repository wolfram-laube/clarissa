#!/usr/bin/env python3
"""
Render Mermaid diagrams to SVG images for PDF generation.

This script:
1. Extracts mermaid code blocks from markdown
2. Renders each to SVG using mermaid-cli (mmdc)
3. Replaces mermaid blocks with image references
4. Outputs modified markdown for PDF generation
"""

import sys
import re
import subprocess
import json
from pathlib import Path


def create_puppeteer_config():
    """Create puppeteer config for running in Docker as root."""
    config = {
        "args": ["--no-sandbox", "--disable-setuid-sandbox"]
    }
    config_path = Path("/tmp/puppeteer-config.json")
    config_path.write_text(json.dumps(config))
    return config_path


def extract_mermaid_blocks(content: str) -> list:
    """Extract all mermaid code blocks from markdown content."""
    pattern = r'```mermaid\s*\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches


def sanitize_mermaid(mermaid_code: str) -> str:
    """Sanitize mermaid code for rendering."""
    # Remove <br/> and <br> tags that break rendering
    code = re.sub(r'<br\s*/?>', '\\n', mermaid_code)
    # Ensure proper line endings
    code = code.strip()
    return code


def render_mermaid_to_svg(mermaid_code: str, output_path: Path, config_path: Path) -> bool:
    """Render mermaid code to SVG using mermaid-cli."""
    # Write mermaid code to temp file
    mmd_file = output_path.with_suffix('.mmd')
    mmd_file.write_text(sanitize_mermaid(mermaid_code))
    
    svg_file = output_path.with_suffix('.svg')
    
    try:
        result = subprocess.run(
            ['mmdc', '-i', str(mmd_file), '-o', str(svg_file), 
             '-b', 'transparent', '-p', str(config_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0 and svg_file.exists():
            return True
        else:
            print(f"  ✗ Failed {output_path.stem}: {result.stderr[:200] if result.stderr else 'Unknown error'}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout rendering {output_path.stem}")
        return False
    except FileNotFoundError:
        print("  ✗ mmdc not found. Install with: npm install -g @mermaid-js/mermaid-cli")
        return False


def replace_mermaid_with_images(content: str, diagram_dir: Path) -> str:
    """Replace mermaid blocks with image references."""
    pattern = r'```mermaid\s*\n(.*?)```'
    
    def replace_block(match, counter=[0]):
        counter[0] += 1
        svg_file = diagram_dir / f"diagram-{counter[0]}.svg"
        if svg_file.exists():
            # Use relative path for pandoc
            return f'![Diagram {counter[0]}]({svg_file})'
        else:
            # Keep original if rendering failed
            return match.group(0)
    
    return re.sub(pattern, replace_block, content, flags=re.DOTALL)


def main():
    if len(sys.argv) < 4:
        print("Usage: render_mermaid_images.py <input.md> <output.md> <diagram_dir>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    diagram_dir = Path(sys.argv[3])
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    diagram_dir.mkdir(parents=True, exist_ok=True)
    
    content = input_file.read_text()
    mermaid_blocks = extract_mermaid_blocks(content)
    
    print(f"Rendering mermaid diagrams from {input_file}...")
    
    if not mermaid_blocks:
        print("No mermaid blocks found, copying input to output")
        output_file.write_text(content)
        return
    
    # Create puppeteer config for Docker/root execution
    config_path = create_puppeteer_config()
    
    # Render each diagram
    success_count = 0
    for i, mermaid_code in enumerate(mermaid_blocks, 1):
        svg_path = diagram_dir / f"diagram-{i}"
        if render_mermaid_to_svg(mermaid_code, svg_path, config_path):
            print(f"  ✓ Rendered diagram-{i}.svg")
            success_count += 1
    
    print(f"Rendered {success_count}/{len(mermaid_blocks)} diagrams")
    
    # Replace mermaid blocks with image references
    modified_content = replace_mermaid_with_images(content, diagram_dir)
    output_file.write_text(modified_content)
    
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    main()
