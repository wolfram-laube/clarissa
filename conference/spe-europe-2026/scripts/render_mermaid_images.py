#!/usr/bin/env python3
"""
Render Mermaid diagrams to SVG images for PDF generation.
Version 2: Improved puppeteer/chromium handling for Docker.
"""

import sys
import re
import subprocess
import json
import os
from pathlib import Path


def extract_mermaid_blocks(content: str) -> list:
    """Extract all mermaid code blocks from markdown content."""
    pattern = r'```mermaid\s*\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches


def sanitize_mermaid(mermaid_code: str) -> str:
    """Sanitize mermaid code for rendering."""
    # Remove <br/> and <br> tags - these break sequence diagrams
    code = re.sub(r'<br\s*/?>', ' ', mermaid_code)
    code = code.replace('&nbsp;', ' ')
    code = code.strip()
    return code


def render_mermaid_to_svg(mermaid_code: str, output_path: Path) -> bool:
    """Render mermaid code to SVG using mermaid-cli."""
    mmd_file = output_path.with_suffix('.mmd')
    svg_file = output_path.with_suffix('.svg')
    
    # Write sanitized mermaid code
    sanitized = sanitize_mermaid(mermaid_code)
    mmd_file.write_text(sanitized)
    
    # Create puppeteer config in same directory
    config = {"args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]}
    config_path = output_path.parent / "puppeteer.json"
    config_path.write_text(json.dumps(config))
    
    try:
        # Find chromium
        chromium_paths = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']
        chromium_path = None
        for p in chromium_paths:
            if os.path.exists(p):
                chromium_path = p
                break
        
        env = os.environ.copy()
        if chromium_path:
            env['PUPPETEER_EXECUTABLE_PATH'] = chromium_path
        
        result = subprocess.run(
            ['mmdc', '-i', str(mmd_file), '-o', str(svg_file), '-p', str(config_path)],
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        if svg_file.exists() and svg_file.stat().st_size > 100:
            return True
        else:
            print(f"  ✗ {output_path.stem}: {result.stderr[:200] if result.stderr else 'No output'}")
            return False
            
    except Exception as e:
        print(f"  ✗ {output_path.stem}: {str(e)[:100]}")
        return False


def replace_mermaid_with_images(content: str, diagram_dir: Path, rendered: set) -> str:
    """Replace mermaid blocks with image references."""
    pattern = r'```mermaid\s*\n(.*?)```'
    counter = [0]
    
    def replacer(match):
        counter[0] += 1
        if counter[0] in rendered:
            return f'![Diagram {counter[0]}]({diagram_dir}/diagram-{counter[0]}.svg)'
        return match.group(0)  # Keep original if not rendered
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)


def main():
    if len(sys.argv) < 4:
        print("Usage: render_mermaid_images.py <input.md> <output.md> <diagram_dir>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    diagram_dir = Path(sys.argv[3])
    
    diagram_dir.mkdir(parents=True, exist_ok=True)
    
    content = input_file.read_text()
    blocks = extract_mermaid_blocks(content)
    
    print(f"Found {len(blocks)} mermaid blocks")
    
    if not blocks:
        output_file.write_text(content)
        return
    
    rendered = set()
    for i, block in enumerate(blocks, 1):
        path = diagram_dir / f"diagram-{i}"
        if render_mermaid_to_svg(block, path):
            print(f"  ✓ diagram-{i}.svg")
            rendered.add(i)
    
    print(f"Rendered {len(rendered)}/{len(blocks)}")
    
    modified = replace_mermaid_with_images(content, diagram_dir, rendered)
    output_file.write_text(modified)


if __name__ == "__main__":
    main()
