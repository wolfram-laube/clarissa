#!/usr/bin/env python3
"""
render_diagrams.py - Render all Mermaid diagrams to SVG and PNG.
Requires: mermaid-cli (mmdc) with Chromium/Puppeteer
"""
import subprocess
import sys
from pathlib import Path


def render_mermaid(input_path: Path, output_svg: Path, output_png: Path) -> bool:
    """Render a .mmd file to SVG and PNG."""
    config_path = input_path.parent / "mermaid.config.json"
    config_args = ["-c", str(config_path)] if config_path.exists() else []
    
    # Render SVG
    try:
        result = subprocess.run(
            ["mmdc", "-i", str(input_path), "-o", str(output_svg), "-b", "transparent"] + config_args,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"   ❌ SVG failed: {result.stderr[:200]}")
            return False
    except FileNotFoundError:
        print("   ❌ mmdc not found - install @mermaid-js/mermaid-cli")
        return False
    except subprocess.TimeoutExpired:
        print("   ❌ Timeout rendering SVG")
        return False
    
    # Render PNG (scale 2x for quality)
    try:
        result = subprocess.run(
            ["mmdc", "-i", str(input_path), "-o", str(output_png), "-s", "2", "-b", "white"] + config_args,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"   ❌ PNG failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ Timeout rendering PNG")
        return False
    
    return True


def main():
    base = Path("conference/spe-europe-2026")
    diagrams_dir = base / "diagrams"
    
    if not diagrams_dir.exists():
        print(f"❌ Diagrams directory not found: {diagrams_dir}")
        sys.exit(1)
    
    mmd_files = list(diagrams_dir.glob("*.mmd"))
    print(f"📊 Found {len(mmd_files)} Mermaid diagrams")
    
    success, failed = 0, 0
    
    for mmd_file in sorted(mmd_files):
        name = mmd_file.stem
        svg_out = diagrams_dir / f"{name}.svg"
        png_out = diagrams_dir / f"{name}.png"
        
        print(f"   🔄 {name}.mmd → .svg + .png")
        
        if render_mermaid(mmd_file, svg_out, png_out):
            print(f"   ✅ {name}")
            success += 1
        else:
            failed += 1
    
    print(f"\n📊 Results: {success} success, {failed} failed")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
