#!/usr/bin/env python3
"""
Check that mkdocs.yml nav references match actual files in docs/.

Exit codes:
  0 - All nav references valid
  1 - Missing files or orphaned docs found
"""

import sys
from pathlib import Path

import yaml


def main():
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    mkdocs_path = project_root / "mkdocs.yml"

    if not mkdocs_path.exists():
        print("ERROR: mkdocs.yml not found")
        sys.exit(1)

    with open(mkdocs_path) as f:
        config = yaml.safe_load(f)

    # Extract all file references from nav
    nav_files = set()

    def extract_nav_files(nav_item):
        if isinstance(nav_item, str):
            nav_files.add(nav_item)
        elif isinstance(nav_item, dict):
            for value in nav_item.values():
                extract_nav_files(value)
        elif isinstance(nav_item, list):
            for item in nav_item:
                extract_nav_files(item)

    extract_nav_files(config.get("nav", []))

    # Get actual docs (excluding i18n source files)
    actual_files = set()
    for md_file in docs_dir.rglob("*.md"):
        rel_path = md_file.relative_to(docs_dir)
        # Skip i18n templates/translations (not direct docs)
        if "i18n/templates" in str(rel_path) or "i18n/translations" in str(rel_path):
            continue
        actual_files.add(str(rel_path))

    # Files generated at CI time (not in repo but valid nav entries)
    # Files generated at CI time by build_i18n_docs.py
    generated_files = {
        # Cheatsheets (markdown)
        "guides/contributing/cheatsheet-en.md",
        "guides/contributing/cheatsheet-de.md",
        "guides/contributing/cheatsheet-vi.md",
        "guides/contributing/cheatsheet-ar.md",
        "guides/contributing/cheatsheet-is.md",
        # HTML files (slides, selector)
        "guides/contributing/index.html",
        "guides/contributing/workflow-slides-en.html",
        "guides/contributing/workflow-slides-de.html",
        "guides/contributing/workflow-slides-vi.html",
        "guides/contributing/workflow-slides-ar.html",
        "guides/contributing/workflow-slides-is.html",
    }

    # Check for missing files (in nav but not in docs/)
    missing = []
    for nav_file in nav_files:
        full_path = docs_dir / nav_file
        if not full_path.exists() and nav_file not in generated_files:
            missing.append(nav_file)

    # Check for orphaned files (in docs/ but not in nav)
    # Exclude known non-nav files
    excluded_patterns = {
        "i18n/",  # i18n source files
        "architecture/adr/ADR-000",  # Template, optional
    }
    orphaned = []
    for actual_file in actual_files:
        if actual_file not in nav_files:
            if not any(excl in actual_file for excl in excluded_patterns):
                orphaned.append(actual_file)

    # Report
    errors = False

    if missing:
        errors = True
        print("❌ FILES IN NAV BUT MISSING FROM docs/:")
        for f in sorted(missing):
            print(f"   - {f}")
        print()

    if orphaned:
        # Orphaned is a warning, not error
        print("⚠️  FILES IN docs/ BUT NOT IN NAV (orphaned):")
        for f in sorted(orphaned):
            print(f"   - {f}")
        print()

    if not missing and not orphaned:
        print(f"✅ MkDocs nav is in sync ({len(nav_files)} entries)")

    if errors:
        print("Fix mkdocs.yml nav to match actual files.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
