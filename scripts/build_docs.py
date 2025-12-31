#!/usr/bin/env python3
"""
Build documentation site for CLARISSA.

This script:
1. Copies/generates documentation files to site_docs/
2. Converts LaTeX paper to HTML (if pandoc available)
3. Prepares everything for MkDocs build

Usage:
    python scripts/build_docs.py
"""

import shutil
import subprocess
from pathlib import Path


def main():
    root = Path(__file__).parent.parent
    docs_src = root / "site_docs"
    
    # Create directory structure
    dirs = [
        "getting-started",
        "architecture/adr", 
        "development",
        "conference",
        "assets",
    ]
    for d in dirs:
        (docs_src / d).mkdir(parents=True, exist_ok=True)
    
    print("📂 Copying documentation files...")
    
    # Copy ADRs
    adr_src = root / "docs" / "adr"
    adr_dst = docs_src / "architecture" / "adr"
    if adr_src.exists():
        for f in adr_src.glob("ADR-*.md"):
            shutil.copy(f, adr_dst / f.name)
            print(f"   ✓ {f.name}")
    
    # Copy main docs
    copy_map = {
        "README.md": "index.md",
        "CHANGELOG.md": "changelog.md",
        "CONTRIBUTING.md": "development/contributing.md",
    }
    for src, dst in copy_map.items():
        src_path = root / src
        if src_path.exists():
            # Read, adjust links, write
            content = src_path.read_text()
            # Fix relative links for MkDocs
            content = content.replace("](docs/adr/", "](architecture/adr/")
            content = content.replace("](CHANGELOG.md)", "](changelog.md)")
            content = content.replace("](CONTRIBUTING.md)", "](development/contributing.md)")
            (docs_src / dst).write_text(content)
            print(f"   ✓ {src} → {dst}")
    
    # Copy conference assets
    conf_src = root / "conference" / "ijacsa-2026"
    assets_dst = docs_src / "assets"
    if conf_src.exists():
        for f in conf_src.glob("CLARISSA_*.pdf"):
            shutil.copy(f, assets_dst / f.name)
            print(f"   ✓ {f.name}")
        
        # Copy from supplementary
        supp = conf_src / "supplementary"
        if supp.exists():
            for f in supp.glob("*.pdf"):
                shutil.copy(f, assets_dst / f.name)
                print(f"   ✓ {f.name}")
    
    # Try to convert LaTeX to HTML
    tex_file = conf_src / "CLARISSA_Paper_IJACSA.tex" if conf_src else None
    if tex_file and tex_file.exists():
        print("\n📄 Converting LaTeX to HTML...")
        try:
            result = subprocess.run(
                ["pandoc", str(tex_file), "-o", str(assets_dst / "CLARISSA_Paper_IJACSA.html"),
                 "--standalone", "--toc", "--metadata", "title=CLARISSA Paper"],
                capture_output=True, text=True, cwd=conf_src
            )
            if result.returncode == 0:
                print("   ✓ CLARISSA_Paper_IJACSA.html")
            else:
                print(f"   ⚠ pandoc warning: {result.stderr[:200]}")
        except FileNotFoundError:
            print("   ⚠ pandoc not found, skipping HTML conversion")
    
    print("\n✅ Docs preparation complete!")
    print(f"   Output: {docs_src}")
    print("\n   Next: mkdocs build")


if __name__ == "__main__":
    main()
