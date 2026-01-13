#!/usr/bin/env python3
"""LLM-based document merge for SPE Europe 2026."""
import os
import anthropic
from docx import Document
from pathlib import Path

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def read_file(path):
    return Path(path).read_text(encoding='utf-8') if Path(path).exists() else ""

print("Reading sources...")
base = Path("conference/spe-europe-2026")

doug = extract_docx(str(base / "sources/doug/SPE_Meeting_Abstract_v6_2_in_Submission_Form.docx"))
wolfram = read_file(str(base / "sources/wolfram/abstract-merged.md"))
synthesis = read_file(str(base / "abstract-synthesis.md"))

print(f"  Doug: {len(doug)} chars, Wolfram: {len(wolfram)} chars")

print("\nCalling Claude API...")
client = anthropic.Anthropic()

prompt = f"""Merge these SPE conference paper contributions into ONE comprehensive Markdown document.

## Doug's SPE Form:
{doug}

## Wolfram's Draft with Diagrams:
{wolfram}

## Current Synthesis:
{synthesis}

## Output Requirements:
1. Pure Markdown with mermaid code blocks for diagrams (use triple backticks with mermaid)
2. SPE structure: Abstract, Objectives, Methods, Results, Novelty, References
3. Include ALL Mermaid diagrams from Wolfram's version
4. Include comparison table (Envoy vs CLARISSA)
5. Authors: Douglas Perschke (Stone Ridge Technology), Michal Matejka (Independent Consultant), Wolfram Laube (Independent Researcher)
6. Full paper length (3000-4000 words)

Output ONLY the Markdown, no explanations."""

msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,
    messages=[{"role": "user", "content": prompt}]
)

merged = msg.content[0].text

out_dir = base / "merged"
out_dir.mkdir(exist_ok=True)
(out_dir / "abstract-merged.md").write_text(merged)

print(f"Merged: {len(merged)} chars saved to {out_dir / 'abstract-merged.md'}")
