#!/usr/bin/env python3
"""
Render Mermaid diagrams to PNG images for PDF generation.
"""

import re
import subprocess
import sys
import os
import json
from pathlib import Path


def sanitize_mermaid(code: str) -> str:
    """Clean mermaid code for rendering."""
    # Remove <br/> and <br> tags - these break sequence diagrams
    code = re.sub(r'<br\s*/?>', '\\n', code)
    # Remove HTML entities
    code = code.replace('&amp;', '&')
    code = code.replace('&lt;', '<')
    code = code.replace('&gt;', '>')
    return code


def render_mermaid_to_png(mermaid_code: str, output_path: Path) -> bool:
    """Render mermaid code to PNG using mmdc."""
    mmd_file = output_path.with_suffix('.mmd')
    png_file = output_path.with_suffix('.png')
    
    # Write mermaid code
    clean_code = sanitize_mermaid(mermaid_code)
    mmd_file.write_text(clean_code)
    
    # Create puppeteer config for headless Chrome
    config = {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
    config_path = output_path.parent / "puppeteer.json"
    config_path.write_text(json.dumps(config))
    
    try:
        # Set up environment for chromium
        env = os.environ.copy()
        chromium_paths = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']
        chromium_path = None
        for p in chromium_paths:
            if os.path.exists(p):
                chromium_path = p
                break
        
        if chromium_path:
            env['PUPPETEER_EXECUTABLE_PATH'] = chromium_path
        
        # Render directly to PNG with larger scale for quality
        result = subprocess.run(
            ['mmdc', '-i', str(mmd_file), '-o', str(png_file), '-p', str(config_path), '-s', '2'],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )
        
        if png_file.exists() and png_file.stat().st_size > 100:
            return True
        else:
            print(f"  ✗ {output_path.stem}: {result.stderr[:200] if result.stderr else 'No output'}")
            return False
    except Exception as e:
        print(f"  ✗ {output_path.stem}: {str(e)[:100]}")
        return False


def replace_mermaid_with_images(content: str, diagram_dir: Path, rendered: set) -> str:
    """Replace mermaid blocks with image references."""
    pattern = r'```mermaid\s*([\s\S]*?)```'
    counter = [0]
    
    def replacer(match):
        counter[0] += 1
        if counter[0] in rendered:
            return f'![Diagram {counter[0]}]({diagram_dir}/diagram-{counter[0]}.png)'
        return match.group(0)  # Keep original if not rendered
    
    return re.sub(pattern, replacer, content)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: render_mermaid_images.py <input.md> <output.md> <diagram_dir>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    diagram_dir = Path(sys.argv[3])
    
    diagram_dir.mkdir(parents=True, exist_ok=True)
    
    content = input_file.read_text()
    
    # Find all mermaid blocks
    pattern = r'```mermaid\s*([\s\S]*?)```'
    blocks = re.findall(pattern, content)
    
    print(f"Found {len(blocks)} mermaid blocks")
    
    # Render each block to PNG
    rendered = set()
    for i, block in enumerate(blocks, 1):
        path = diagram_dir / f"diagram-{i}"
        if render_mermaid_to_png(block, path):
            print(f"  ✓ diagram-{i}.png")
            rendered.add(i)
    
    print(f"Rendered {len(rendered)}/{len(blocks)}")
    
    # Replace mermaid blocks with image references
    modified = replace_mermaid_with_images(content, diagram_dir, rendered)
    output_file.write_text(modified)
