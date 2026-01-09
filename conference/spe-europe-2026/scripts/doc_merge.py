#!/usr/bin/env python3
"""
doc_merge.py - LLM-powered semantic document merge

Usage:
    python doc_merge.py --sources sources/ --canonical canonical/abstract.md --output merged/

Environment:
    ANTHROPIC_API_KEY or OPENAI_API_KEY must be set
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Try to import LLM clients
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def convert_docx_to_md(docx_path: Path, output_dir: Path) -> Path:
    """Convert DOCX to Markdown using Pandoc"""
    output_path = output_dir / f"{docx_path.stem}.md"
    
    cmd = [
        "pandoc", str(docx_path),
        "-t", "markdown",
        "-o", str(output_path),
        "--wrap=none",
        "--extract-media", str(output_dir / "media")
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Pandoc conversion failed for {docx_path}: {result.stderr}")
        return None
    
    return output_path


def load_documents(sources_dir: Path, work_dir: Path) -> dict:
    """Load all source documents, converting as needed"""
    documents = {}
    
    for author_dir in sources_dir.iterdir():
        if not author_dir.is_dir():
            continue
        
        author = author_dir.name
        
        for doc_file in author_dir.iterdir():
            if doc_file.suffix == ".docx":
                # Convert DOCX to MD
                md_path = convert_docx_to_md(doc_file, work_dir)
                if md_path:
                    documents[f"{author}/{doc_file.stem}"] = md_path.read_text()
            
            elif doc_file.suffix == ".md":
                documents[f"{author}/{doc_file.stem}"] = doc_file.read_text()
    
    return documents


def call_anthropic(prompt: str, max_tokens: int = 8000) -> str:
    """Call Anthropic Claude API"""
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def call_openai(prompt: str, max_tokens: int = 8000) -> str:
    """Call OpenAI GPT API"""
    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


def call_llm(prompt: str) -> str:
    """Call available LLM API"""
    if HAS_ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
        return call_anthropic(prompt)
    elif HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
        return call_openai(prompt)
    else:
        raise RuntimeError("No LLM API available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")


def compare_documents(base: str, documents: dict) -> dict:
    """Compare documents using LLM"""
    
    prompt = f"""Analyze these document versions for a technical paper merge.

BASE (current canonical version):
<base>
{base[:12000] if base else "No existing base document"}
</base>

CONTRIBUTOR VERSIONS:
"""
    
    for name, content in documents.items():
        prompt += f"\n<{name}>\n{content[:6000]}\n</{name}>\n"
    
    prompt += """
Analyze and output JSON:
{
  "contributors": ["list of contributor names"],
  "unique_contributions": {
    "contributor_name": ["list of unique additions/improvements from this version"]
  },
  "conflicts": [
    {
      "topic": "what the conflict is about",
      "positions": {"contributor1": "their position", "contributor2": "their position"},
      "recommendation": "which to prefer and why"
    }
  ],
  "merge_priority": ["ordered list of contributors by content quality/detail"],
  "summary": "brief summary of differences"
}"""

    response = call_llm(prompt)
    
    # Extract JSON
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        return json.loads(response[start:end])
    except json.JSONDecodeError:
        return {"raw_response": response, "error": "Could not parse JSON"}


def merge_documents(base: str, documents: dict, comparison: dict) -> dict:
    """Merge documents using LLM"""
    
    prompt = f"""You are merging multiple versions of a technical document about CLARISSA, 
a conversational AI system for reservoir simulation.

MERGE ANALYSIS:
{json.dumps(comparison, indent=2)}

BASE VERSION (current canonical):
<base>
{base if base else "No existing base - create unified version from inputs"}
</base>

CONTRIBUTOR VERSIONS:
"""
    
    for name, content in documents.items():
        prompt += f"\n<{name}>\n{content}\n</{name}>\n"
    
    prompt += """
MERGE RULES:
1. Include ALL unique contributions from each version
2. For Doug (petroleum engineer): Trust domain expertise, use his reservoir engineering terminology
3. For Wolfram (software architect): Trust technical architecture, use his system design
4. For Mike: Trust business/practical perspectives
5. Resolve conflicts by preferring more detailed/specific content
6. Maintain consistent style and terminology throughout
7. Use Markdown formatting
8. Preserve any diagrams/tables in Markdown format

OUTPUT (JSON):
{
  "merged_document": "... complete merged Markdown document ...",
  "incorporation_log": [
    {"from": "contributor", "what": "description of incorporated content"}
  ],
  "conflicts_resolved": [
    {"topic": "...", "resolution": "...", "rationale": "..."}
  ],
  "warnings": ["any concerns or items needing human review"]
}"""

    response = call_llm(prompt)
    
    # Extract JSON
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        return json.loads(response[start:end])
    except json.JSONDecodeError:
        # If JSON parsing fails, treat the response as the merged document
        return {
            "merged_document": response,
            "incorporation_log": [],
            "conflicts_resolved": [],
            "warnings": ["Could not parse structured response, using raw output"]
        }


def main():
    parser = argparse.ArgumentParser(description="LLM-powered document merge")
    parser.add_argument("--sources", required=True, help="Directory with author subdirs")
    parser.add_argument("--canonical", help="Path to current canonical document")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--compare-only", action="store_true", help="Only compare, don't merge")
    args = parser.parse_args()
    
    sources_dir = Path(args.sources)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    work_dir = output_dir / "work"
    work_dir.mkdir(exist_ok=True)
    
    # Load base document
    base_content = ""
    if args.canonical and Path(args.canonical).exists():
        base_content = Path(args.canonical).read_text()
    
    print("=== Loading source documents ===")
    documents = load_documents(sources_dir, work_dir)
    
    if not documents:
        print("No source documents found!")
        sys.exit(1)
    
    print(f"Found {len(documents)} documents:")
    for name in documents:
        print(f"  - {name}")
    
    print("\n=== Comparing documents (LLM) ===")
    comparison = compare_documents(base_content, documents)
    
    comparison_path = output_dir / "comparison-report.json"
    comparison_path.write_text(json.dumps(comparison, indent=2))
    print(f"Comparison saved to: {comparison_path}")
    
    if "summary" in comparison:
        print(f"\nSummary: {comparison['summary']}")
    
    if args.compare_only:
        print("\n--compare-only specified, stopping here")
        return
    
    print("\n=== Merging documents (LLM) ===")
    merge_result = merge_documents(base_content, documents, comparison)
    
    # Save merged document
    merged_path = output_dir / "abstract-merged.md"
    merged_path.write_text(merge_result["merged_document"])
    print(f"Merged document saved to: {merged_path}")
    
    # Save merge log
    log_path = output_dir / "merge-log.json"
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "sources": list(documents.keys()),
        "incorporation_log": merge_result.get("incorporation_log", []),
        "conflicts_resolved": merge_result.get("conflicts_resolved", []),
        "warnings": merge_result.get("warnings", [])
    }
    log_path.write_text(json.dumps(log_entry, indent=2))
    print(f"Merge log saved to: {log_path}")
    
    # Print summary
    print("\n=== Merge Summary ===")
    print(f"Incorporated: {len(merge_result.get('incorporation_log', []))} items")
    print(f"Conflicts resolved: {len(merge_result.get('conflicts_resolved', []))}")
    
    if merge_result.get("warnings"):
        print("\n⚠️  Warnings:")
        for w in merge_result["warnings"]:
            print(f"  - {w}")
    
    print("\n✅ Merge complete! Review the output before committing.")


if __name__ == "__main__":
    main()
