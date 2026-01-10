#!/usr/bin/env python3
"""doc_compare.py - Compare document versions using LLM (Anthropic or OpenAI)"""
import os
import json
from pathlib import Path


def call_anthropic(prompt, max_tokens=4000):
    """Try Anthropic API"""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def call_openai(prompt, max_tokens=4000):
    """Try OpenAI API"""
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def call_llm(prompt, max_tokens=4000):
    """Call LLM - tries Anthropic first, falls back to OpenAI on ANY error"""
    
    # Try Anthropic first
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("Trying Anthropic...")
            result = call_anthropic(prompt, max_tokens)
            print("✅ Anthropic succeeded")
            return result
        except Exception as e:
            print(f"⚠️ Anthropic failed: {e}")
            print("Falling back to OpenAI...")
    
    # Fallback to OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        try:
            print("Trying OpenAI...")
            result = call_openai(prompt, max_tokens)
            print("✅ OpenAI succeeded")
            return result
        except Exception as e:
            print(f"❌ OpenAI also failed: {e}")
            raise
    
    raise RuntimeError("No working LLM API available")


def compare_documents():
    # Check if any API key is available
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ No LLM API key set (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        Path("comparison-report.json").write_text(json.dumps({"status": "no_api_key"}))
        return

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
Analyze and output JSON only (no other text):
{
  "contributors": ["list of contributor names"],
  "unique_contributions": {"contributor_name": ["list of unique additions"]},
  "conflicts": [{"topic": "...", "positions": {"v1": "...", "v2": "..."}, "recommendation": "..."}],
  "merge_strategy": "description of recommended merge approach",
  "summary": "brief summary of differences"
}"""

    print("Calling LLM API for comparison...")
    result_text = call_llm(prompt)

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
