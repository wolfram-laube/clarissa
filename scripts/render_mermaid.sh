#!/usr/bin/env bash
set -euo pipefail

IN_DIR="docs/architecture/diagrams"
OUT_DIR="docs/architecture/rendered"
PUPPETEER_CFG="$(mktemp /tmp/puppeteer-XXXXXX.json)"
mkdir -p "$OUT_DIR"

# Puppeteer config for no-sandbox (required in CI Docker containers)
cat > "$PUPPETEER_CFG" << 'JSON'
{"args":["--no-sandbox","--disable-setuid-sandbox"]}
JSON

MMDC="npx --yes @mermaid-js/mermaid-cli"

# Render all .mmd to .svg using mermaid-cli (mmdc)
shopt -s nullglob
files=("$IN_DIR"/*.mmd)
if [ ${#files[@]} -eq 0 ]; then
  echo "No .mmd files found in $IN_DIR — skipping render."
  exit 0
fi

for f in "${files[@]}"; do
  base="$(basename "$f" .mmd)"
  echo "Rendering $f -> $OUT_DIR/$base.svg"
  $MMDC -i "$f" -o "$OUT_DIR/$base.svg" --puppeteerConfigFile "$PUPPETEER_CFG" || exit 1
done

# Generate gallery indices
python scripts/generate_diagram_gallery.py
