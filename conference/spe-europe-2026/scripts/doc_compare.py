#!/usr/bin/env python3
"""doc_compare.py - Compare document versions using LLM"""
import os
import json
import anthropic
from pathlib import Path


def compare_documents():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️ ANTHROPIC_API_KEY not set, skipping comparison")
        Path("comparison-report.json").write_text(json.dumps({"status": "no_api_key"}))
        return

    client = anthropic.Anthropic(api_key=api_key)

    # Read canonical (if exists)
    canonical_path = Path("conference/spe-europe-2026/canonical/abstract.md")
    base_content = canonical_path.read_text() if canonical_path.exists() else ""

    # Read all normalized inputs
    inputs = {}
    normalized = Path("normalized")
    if normalized.exists():
        for md_file in normalized.glob("*.md"):
            inputs[md_file.stem] = md_file.read_text()

    if not inputs:
        print("No input files to compare")
        Path("comparison-report.json").write_text(json.dumps({"status": "no_inputs"}))
        return

    prompt = f"""Analyze these document versions for a technical paper merge.

BASE (current canonical version):
<base>
{base_content[:12000] if base_content else "No existing canonical version"}
</base>

CONTRIBUTOR VERSIONS:
"""
    for name, content in inputs.items():
        prompt += f"\n<{name}>\n{content[:5000]}\n</{name}>\n"

    prompt += """
Analyze and output JSON:
{
  "contributors": ["list of contributor names"],
  "unique_contributions": {"contributor_name": ["list of unique additions"]},
  "conflicts": [{"topic": "...", "positions": {"v1": "...", "v2": "..."}, "recommendation": "..."}],
  "merge_strategy": "description of recommended merge approach",
  "summary": "brief summary of differences"
}"""

    print("Calling Claude API for comparison...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.content[0].text

    try:
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        result = json.loads(result_text[start:end])
    except Exception as e:
        result = {"raw_analysis": result_text, "parse_error": str(e)}

    Path("comparison-report.json").write_text(json.dumps(result, indent=2))

    print("=== COMPARISON REPORT ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    compare_documents()
