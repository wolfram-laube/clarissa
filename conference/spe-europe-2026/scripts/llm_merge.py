#!/usr/bin/env python3
"""LLM-based document merge for SPE Europe 2026 with Anthropic/OpenAI fallback."""
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
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    print("📖 Reading sources...")
    base = Path("conference/spe-europe-2026")

    doug = extract_docx(str(base / "sources/doug/SPE_Meeting_Abstract_v6_2_in_Submission_Form.docx"))
    wolfram = read_file(str(base / "sources/wolfram/abstract-merged.md"))
    synthesis = read_file(str(base / "abstract-synthesis.md"))

    print(f"   Doug: {len(doug)} chars, Wolfram: {len(wolfram)} chars, Synthesis: {len(synthesis)} chars")

    prompt = f"""Merge these SPE conference paper contributions into ONE comprehensive Markdown document.

## Doug's SPE Submission Form:
{doug}

## Wolfram's Draft with Architecture and Diagrams:
{wolfram}

## Current Synthesis (for reference):
{synthesis}

## Output Requirements:
1. Pure Markdown with mermaid code blocks for diagrams (use triple backticks with mermaid language tag)
2. SPE structure: Title, Authors, Abstract, 1. Objectives/Scope, 2. Methods/Procedures, 3. Results/Conclusions, 4. Novelty, References
3. Include ALL Mermaid diagrams from Wolfram's version (architecture, phases, RIGOR, techstack, comparison)
4. Include the comparison table (Envoy vs CLARISSA)
5. Authors: Douglas Perschke (Stone Ridge Technology, USA), Michal Matejka (Independent Consultant, Houston, USA), Wolfram Laube (Independent Researcher, Austria)
6. Full paper length: 3000-4000 words total
7. Conference: SPE Europe Energy Conference 2026
8. Category: 05 Digital Transformation and AI / 05.6 ML and AI in Subsurface Operations

Output ONLY the merged Markdown document, no explanations or preamble."""

    merged = None
    
    # Try Anthropic first
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("\n🤖 Trying Anthropic Claude API...")
        try:
            merged = call_anthropic(prompt)
            print("   ✅ Anthropic succeeded!")
        except Exception as e:
            print(f"   ⚠️ Anthropic failed: {e}")
    
    # Fallback to OpenAI
    if merged is None and os.environ.get('OPENAI_API_KEY'):
        print("\n🔄 Falling back to OpenAI GPT-4...")
        try:
            merged = call_openai(prompt)
            print("   ✅ OpenAI succeeded!")
        except Exception as e:
            print(f"   ❌ OpenAI failed: {e}")
            sys.exit(1)
    
    if merged is None:
        print("❌ No API keys available or all APIs failed!")
        sys.exit(1)

    # Save output
    out_dir = base / "merged"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "abstract-merged.md").write_text(merged)

    print(f"\n✅ Merged document saved: {len(merged)} chars")
    print(f"   Location: {out_dir / 'abstract-merged.md'}")

if __name__ == "__main__":
    main()
