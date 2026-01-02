#!/usr/bin/env python3
"""
Build internationalized documentation from templates and translation files.

Usage:
    python scripts/build_i18n_docs.py

This script:
1. Loads Jinja2 templates from docs/i18n/templates/
2. Loads translation YAML files from docs/i18n/translations/
3. Generates localized output files in docs/guides/contributing/
"""

import os
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
I18N_DIR = PROJECT_ROOT / "docs" / "i18n"
TEMPLATES_DIR = I18N_DIR / "templates"
TRANSLATIONS_DIR = I18N_DIR / "translations"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "guides" / "contributing"


def load_translations() -> dict:
    """Load all translation YAML files."""
    translations = {}
    
    for yaml_file in TRANSLATIONS_DIR.glob("*.yaml"):
        lang_code = yaml_file.stem
        with open(yaml_file, "r", encoding="utf-8") as f:
            translations[lang_code] = yaml.safe_load(f)
        print(f"  Loaded: {lang_code}.yaml")
    
    return translations


def merge_with_fallback(translation: dict, fallback: dict) -> dict:
    """Recursively merge translation with English fallback for missing keys."""
    result = {}
    
    for key, fallback_value in fallback.items():
        if key in translation:
            if isinstance(fallback_value, dict) and isinstance(translation[key], dict):
                result[key] = merge_with_fallback(translation[key], fallback_value)
            else:
                result[key] = translation[key]
        else:
            result[key] = fallback_value
    
    # Include any keys in translation not in fallback
    for key in translation:
        if key not in result:
            result[key] = translation[key]
    
    return result


def build_language_selector(env: Environment, translations: dict) -> None:
    """Build the language selector index.html."""
    template = env.get_template("index.html.jinja2")
    
    # Collect all languages
    languages = []
    for lang_code, trans in translations.items():
        meta = trans.get("meta", {})
        languages.append({
            "code": lang_code,
            "name": meta.get("language_name", lang_code),
            "native": meta.get("language_native", lang_code),
            "flag": meta.get("flag_emoji", "🌐"),
            "direction": meta.get("direction", "ltr"),
            "font_family": meta.get("font_family", "Space Grotesk"),
        })
    
    # Sort: English first, then alphabetically
    languages.sort(key=lambda x: (x["code"] != "en", x["name"]))
    
    # Use English for selector text
    en_trans = translations.get("en", {})
    selector = en_trans.get("selector", {})
    
    output = template.render(
        languages=languages,
        selector=selector,
        all_translations=translations,
    )
    
    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(output, encoding="utf-8")
    print(f"  Generated: index.html")


def build_slides(env: Environment, translations: dict, fallback: dict) -> None:
    """Build workflow slides for all languages."""
    template = env.get_template("workflow-slides.html.jinja2")
    
    for lang_code, trans in translations.items():
        # Merge with English fallback
        merged = merge_with_fallback(trans, fallback)
        meta = merged.get("meta", {})
        
        # Get all language codes for language switcher
        all_langs = [
            {
                "code": lc,
                "name": translations[lc].get("meta", {}).get("language_name", lc)[:2].upper()
            }
            for lc in sorted(translations.keys(), key=lambda x: (x != "en", x))
        ]
        
        output = template.render(
            t=merged,
            meta=meta,
            lang_code=lang_code,
            all_langs=all_langs,
        )
        
        output_path = OUTPUT_DIR / f"workflow-slides-{lang_code}.html"
        output_path.write_text(output, encoding="utf-8")
        print(f"  Generated: workflow-slides-{lang_code}.html")


def build_cheatsheets(env: Environment, translations: dict, fallback: dict) -> None:
    """Build cheatsheet markdown files for all languages."""
    template = env.get_template("cheatsheet.md.jinja2")
    
    for lang_code, trans in translations.items():
        # Merge with English fallback
        merged = merge_with_fallback(trans, fallback)
        meta = merged.get("meta", {})
        
        output = template.render(
            t=merged,
            meta=meta,
            lang_code=lang_code,
        )
        
        output_path = OUTPUT_DIR / f"cheatsheet-{lang_code}.md"
        output_path.write_text(output, encoding="utf-8")
        print(f"  Generated: cheatsheet-{lang_code}.md")


def main():
    print("=" * 60)
    print("CLARISSA i18n Documentation Builder")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check directories exist
    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}")
        sys.exit(1)
    
    if not TRANSLATIONS_DIR.exists():
        print(f"ERROR: Translations directory not found: {TRANSLATIONS_DIR}")
        sys.exit(1)
    
    # Setup Jinja2
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    # Load translations
    print("\nLoading translations...")
    translations = load_translations()
    
    if "en" not in translations:
        print("ERROR: English translation (en.yaml) is required as fallback!")
        sys.exit(1)
    
    fallback = translations["en"]
    
    # Build outputs
    print("\nBuilding language selector...")
    build_language_selector(env, translations)
    
    print("\nBuilding workflow slides...")
    build_slides(env, translations, fallback)
    
    print("\nBuilding cheatsheets...")
    build_cheatsheets(env, translations, fallback)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Built documentation for {len(translations)} languages:")
    for lang_code in sorted(translations.keys()):
        meta = translations[lang_code].get("meta", {})
        print(f"   {meta.get('flag_emoji', '🌐')} {meta.get('language_native', lang_code)} ({lang_code})")
    print("=" * 60)


if __name__ == "__main__":
    main()
