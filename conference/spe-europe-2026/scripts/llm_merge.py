#!/usr/bin/env python3
"""LLM-based document merge for SPE Europe 2026 with Anthropic/OpenAI fallback.
Version 2: Improved prompt for proper list formatting and reduced redundancy."""
import os
import sys
import re
from docx import Document
from pathlib import Path

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def read_file(path):
    return Path(path).read_text(encoding='utf-8') if Path(path).exists() else ""

def clean_llm_output(text):
    """Remove LLM artifacts like ```markdown wrappers."""
    text = re.sub(r'^```markdown\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()

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

### Structure (SPE format):
1. Title: # CLARISSA: A Conversational User Interface for Democratizing Reservoir Simulation
2. Conference info and Authors (as bullet list)
3. ## Abstract (comprehensive, ~400 words)
4. ## 1. Objectives and Scope (DIFFERENT from abstract - focus on specific goals, not problem statement)
5. ## 2. Methods, Procedures, Process
   - ### 2.1 System Architecture (with Mermaid flowchart)
   - ### 2.2 Phased Development (with Mermaid flowchart)
   - ### 2.3 Comparison with Prior Work (with Mermaid + comparison table)
6. ## 3. Results, Observations, Conclusions
   - ### 3.1 RIGOR Benchmark Framework (with Mermaid)
   - ### 3.2 Example Interaction (with Mermaid sequence diagram)
   - ### 3.3 Key Capabilities Demonstrated (as NUMBERED LIST with "1. ", "2. ", etc.)
7. ## 4. Novelty and Contribution (as bullet list)
8. ## Technical Stack (with Mermaid flowchart)
9. ## References (as NUMBERED LIST with "1. ", "2. ", etc.)

### Formatting Rules:
- Output PURE Markdown only - NO code fences around the entire document
- Use ```mermaid for diagrams
- Use "- " for unordered lists
- Use "1. ", "2. ", "3. " for ORDERED/NUMBERED lists (Key Capabilities, References)
- Use "---" for section separators
- Bold with **text**

### Content Requirements:
- Include ALL 6 Mermaid diagrams from Wolfram's version
- Include the Envoy vs CLARISSA comparison table
- Section 1 (Objectives) should NOT repeat the Abstract - instead focus on:
  * What CLARISSA specifically aims to achieve
  * What RIGOR benchmark will evaluate
  * Scope limitations (what is NOT covered)
- References must include at minimum:
  1. SPE-221987-MS (Wiegand et al., ADIPEC 2024)
  2. OPM Flow Documentation
  3. At least 2-3 more relevant references (Eclipse documentation, LLM papers, etc.)

### Authors:
- Douglas Perschke, Stone Ridge Technology, USA
- Michal Matejka, Independent Consultant, Houston, USA
- Wolfram Laube, Independent Researcher, Austria

### Conference:
SPE Europe Energy Conference 2026
Category: 05 Digital Transformation and AI
Subcategory: 05.6 ML and AI in Subsurface Operations

CRITICAL: Start directly with # Title - do NOT wrap in ```markdown fence."""

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

    # Clean up LLM output
    merged = clean_llm_output(merged)
    print(f"   Cleaned output: {len(merged)} chars")

    # Save output
    out_dir = base / "merged"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "abstract-merged.md").write_text(merged, encoding='utf-8')

    print(f"\n✅ Merged document saved: {len(merged)} chars")
    print(f"   Location: {out_dir / 'abstract-merged.md'}")

if __name__ == "__main__":
    main()
