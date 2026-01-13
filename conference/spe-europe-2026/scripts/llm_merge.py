#!/usr/bin/env python3
"""LLM-based document merge for SPE Europe 2026 with OpenAI fallback."""
import os
import sys
from docx import Document
from pathlib import Path

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def read_file(path):
    return Path(path).read_text(encoding='utf-8') if Path(path).exists() else ""

def call_anthropic(prompt):
    """Try Anthropic Claude API."""
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

def call_openai(prompt):
    """Fallback to OpenAI GPT-4."""
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    print("Reading sources...")
    base = Path("conference/spe-europe-2026")

    doug = extract_docx(str(base / "sources/doug/SPE_Meeting_Abstract_v6_2_in_Submission_Form.docx"))
    wolfram = read_file(str(base / "sources/wolfram/abstract-merged.md"))
    synthesis = read_file(str(base / "abstract-synthesis.md"))

    print(f"  Doug: {len(doug)} chars, Wolfram: {len(wolfram)} chars, Synthesis: {len(synthesis)} chars")

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
3. Include ALL Mermaid diagrams from Wolfram's version (architecture, phases, RIGOR, techstack, comparison)
4. Include comparison table (Envoy vs CLARISSA)
5. Authors: Douglas Perschke (Stone Ridge Technology), Michal Matejka (Independent Consultant), Wolfram Laube (Independent Researcher)
6. Full paper length (3000-4000 words)
7. Keep the technical depth from Wolfram's version

Output ONLY the Markdown document, no explanations or preamble."""

    merged = None
    
    # Try Anthropic first
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("\nTrying Anthropic Claude API...")
        try:
            merged = call_anthropic(prompt)
            print("  Success with Anthropic!")
        except Exception as e:
            print(f"  Anthropic failed: {e}")
    
    # Fallback to OpenAI
    if merged is None and os.environ.get('OPENAI_API_KEY'):
        print("\nFalling back to OpenAI GPT-4...")
        try:
            merged = call_openai(prompt)
            print("  Success with OpenAI!")
        except Exception as e:
            print(f"  OpenAI failed: {e}")
    
    if merged is None:
        print("\nERROR: Both API calls failed!")
        sys.exit(1)

    # Save output
    out_dir = base / "merged"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "abstract-merged.md").write_text(merged)

    print(f"\nMerged: {len(merged)} chars saved to {out_dir / 'abstract-merged.md'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
