#!/usr/bin/env python3
"""doc_do_merge.py - Merge document versions using LLM (Anthropic or OpenAI)"""
import os
import json
from pathlib import Path
from datetime import datetime


def get_llm_client():
    """Get available LLM client - tries Anthropic first, then OpenAI"""
    
    # Try Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()
            return ("anthropic", client)
        except Exception as e:
            print(f"⚠️ Anthropic not available: {e}")
    
    # Try OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        try:
            import openai
            client = openai.OpenAI()
            return ("openai", client)
        except Exception as e:
            print(f"⚠️ OpenAI not available: {e}")
    
    return (None, None)


def call_llm(client_type, client, prompt, max_tokens=8000):
    """Call LLM API"""
    if client_type == "anthropic":
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    elif client_type == "openai":
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    else:
        raise RuntimeError("No LLM client available")


def merge_documents():
    client_type, client = get_llm_client()
    
    if not client:
        print("❌ No LLM API available (ANTHROPIC_API_KEY or OPENAI_API_KEY required)")
        exit(1)

    print(f"Using LLM: {client_type}")

    # Read canonical
    canonical_path = Path("conference/spe-europe-2026/canonical/abstract.md")
    base_content = canonical_path.read_text() if canonical_path.exists() else ""

    # Read comparison report
    comparison = {}
    comp_path = Path("comparison-report.json")
    if comp_path.exists():
        comparison = json.loads(comp_path.read_text())

    # Read normalized inputs
    inputs = {}
    normalized = Path("normalized")
    if normalized.exists():
        for md_file in normalized.glob("*.md"):
            inputs[md_file.stem] = md_file.read_text()

    if not inputs:
        print("No inputs to merge")
        return

    prompt = f"""You are merging multiple versions of a technical document about CLARISSA,
a conversational AI system for reservoir simulation.

COMPARISON ANALYSIS:
{json.dumps(comparison, indent=2)}

BASE VERSION:
<base>
{base_content[:15000] if base_content else "No existing base - create from inputs"}
</base>

INPUT VERSIONS:
"""
    for name, content in inputs.items():
        prompt += f"\n<{name}>\n{content}\n</{name}>\n"

    prompt += """
MERGE RULES:
1. Include ALL unique contributions from each version
2. Doug (petroleum engineer): Trust domain expertise, reservoir engineering terminology
3. Wolfram (software architect): Trust technical architecture, system design
4. Mike: Trust business/practical perspectives
5. Resolve conflicts by preferring more detailed/specific content
6. Maintain consistent style and terminology
7. Use Markdown formatting

OUTPUT JSON only (no other text):
{
  "merged_document": "... full markdown document ...",
  "incorporation_log": [{"from": "contributor", "what": "description"}],
  "conflicts_resolved": [{"topic": "...", "resolution": "...", "rationale": "..."}]
}"""

    print("Calling LLM API for merge...")
    
    try:
        result_text = call_llm(client_type, client, prompt)
    except Exception as e:
        print(f"❌ LLM API error: {e}")
        raise

    try:
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        result = json.loads(result_text[start:end])
    except Exception as e:
        result = {"merged_document": result_text, "error": str(e)}

    # Write merged document
    merged_doc = result.get("merged_document", "")
    Path("merged-output.md").write_text(merged_doc)

    # Write merge log
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "llm_used": client_type,
        "sources": list(inputs.keys()),
        "incorporation_log": result.get("incorporation_log", []),
        "conflicts_resolved": result.get("conflicts_resolved", [])
    }
    Path("merge-log.json").write_text(json.dumps(log_entry, indent=2))

    print("=== MERGE COMPLETE ===")
    print(f"LLM: {client_type}")
    print(f"Document: {len(merged_doc)} characters")
    print(f"Incorporated: {len(result.get('incorporation_log', []))} items")
    print(f"Conflicts resolved: {len(result.get('conflicts_resolved', []))}")


if __name__ == "__main__":
    merge_documents()
