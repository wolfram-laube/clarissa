#!/usr/bin/env bash
set -euo pipefail

IN_DIR="docs/architecture/diagrams"
OUT_DIR="docs/architecture/rendered"
mkdir -p "$OUT_DIR"

# Render all .mmd to .svg using mermaid-cli (mmdc)
for f in "$IN_DIR"/*.mmd; do
  base="$(basename "$f" .mmd)"
  echo "Rendering $f -> $OUT_DIR/$base.svg"
  mmdc -i "$f" -o "$OUT_DIR/$base.svg" --quiet || exit 1
done


# Generate gallery indices
python scripts/generate_diagram_gallery.py
