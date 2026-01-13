#!/usr/bin/env python3
"""
LLM-powered document merge for SPE Abstract
Uses OpenAI API to intelligently merge multiple author contributions
"""

import os
import sys
import json
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai...")
    os.system("pip install openai --break-system-packages -q")
    from openai import OpenAI

def read_docx(filepath):
    """Extract text from DOCX file"""
    try:
        from docx import Document
    except ImportError:
        os.system("pip install python-docx --break-system-packages -q")
        from docx import Document
    
    doc = Document(filepath)
    return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def read_file(filepath):
    """Read text or markdown file"""
    return Path(filepath).read_text(encoding='utf-8')

def merge_with_llm(sources: dict, api_key: str) -> str:
    """Use LLM to merge multiple document sources"""
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are an expert technical editor merging contributions for an SPE (Society of Petroleum Engineers) conference paper abstract.

Your task is to create a unified, coherent document that:
1. Preserves all unique technical content from each source
2. Follows SPE abstract structure: Abstract, Objectives, Methods, Results, Novelty/Contribution
3. Maintains consistent voice and terminology
4. Removes redundancy while keeping important details
5. Ensures technical accuracy for reservoir simulation domain
6. Keeps Mermaid diagram code blocks intact (```mermaid ... ```)
7. Outputs clean Markdown format

The paper is about CLARISSA - a Conversational Language Agent for Reservoir Simulation."""

    user_prompt = f"""Please merge these contributions into a single cohesive SPE conference abstract.

=== SOURCE 1 (Doug - SPE Submission Form Format) ===
{sources.get('doug', 'No content')}

=== SOURCE 2 (Wolfram - Extended Technical Version) ===
{sources.get('wolfram', 'No content')}

=== SOURCE 3 (Mike - Additional Contributions) ===
{sources.get('mike', 'No content')}

Create a merged document that:
- Uses the SPE structure (Abstract, 1. Objectives, 2. Methods, 3. Results, 4. Novelty)
- Incorporates the technical depth from Wolfram's version
- Includes any unique insights from each contributor
- Keeps all Mermaid diagrams from the sources
- Is suitable for an 8-page conference paper abstract (~3000-4000 words)

Output the merged document in Markdown format."""

    print("Calling OpenAI API for merge...", file=sys.stderr)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=8000,
        temperature=0.3
    )
    
    return response.choices[0].message.content

def main():
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    # Define source paths
    base_path = Path("conference/spe-europe-2026/sources")
    
    sources = {}
    
    # Read Doug's DOCX
    doug_path = base_path / "doug" / "SPE_Meeting_Abstract_v6_2_in_Submission_Form.docx"
    if doug_path.exists():
        print(f"Reading: {doug_path}", file=sys.stderr)
        sources['doug'] = read_docx(doug_path)
    
    # Read Wolfram's MD
    wolfram_path = base_path / "wolfram" / "abstract-merged.md"
    if wolfram_path.exists():
        print(f"Reading: {wolfram_path}", file=sys.stderr)
        sources['wolfram'] = read_file(wolfram_path)
    
    # Read Mike's contributions (any .md files)
    mike_path = base_path / "mike"
    mike_content = []
    for md_file in mike_path.glob("*.md"):
        if md_file.name != "README.md":
            print(f"Reading: {md_file}", file=sys.stderr)
            mike_content.append(read_file(md_file))
    if mike_content:
        sources['mike'] = "\n\n---\n\n".join(mike_content)
    else:
        sources['mike'] = "(No contributions yet)"
    
    # Perform merge
    merged = merge_with_llm(sources, api_key)
    
    # Output merged content
    print(merged)
    
    # Also save to file
    output_path = Path("conference/spe-europe-2026/merged/abstract-merged.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding='utf-8')
    print(f"\nSaved to: {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
