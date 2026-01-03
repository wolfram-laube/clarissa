"""CLARISSA Intent Recognition Module.

This module provides intent classification for natural language reservoir
simulation commands per ADR-009.
"""

from pathlib import Path
import json

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"

def load_taxonomy() -> dict:
    """Load intent taxonomy from JSON file."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)

__all__ = ["load_taxonomy", "TAXONOMY_PATH"]
