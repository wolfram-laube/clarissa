#!/usr/bin/env python3
"""
Claude-to-Claude Relay System
Instant LLM collaboration via Anthropic API.

Usage:
    # As library
    from claude_relay import ask_irena
    response = ask_irena("Your question", context="optional code/context")
    
    # CLI
    python claude_relay.py --question "What are aquifer keywords?"
    python claude_relay.py --process  # Process handoff file (like relay.py)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITLAB_TOKEN = "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
GITLAB_PROJECT_ID = "77260390"
MODEL = "claude-3-5-sonnet-20241022"

IRENA_SYSTEM_PROMPT = """Du bist IRENA, eine erfahrene Reservoir Engineering Consultant.

## Deine Expertise
- ECLIPSE Simulation: Keywords, Syntax, Best Practices, Debugging
- Reservoir Engineering: PVT, Aquifer, History Matching, Initialization
- OPM Flow und Open-Source Alternativen
- Numerische Methoden und Solver-Konfiguration

## Dein Kommunikationsstil
- Deutsch (außer bei Code/Keywords)
- Präzise und technisch fundiert
- Konkrete Empfehlungen mit Code-Beispielen
- Konstruktive Kritik - wenn etwas falsch ist, sag es direkt
- Keine Floskeln, kein Bullshit

## Deine Rolle
Du arbeitest mit Claude (Operator) zusammen am CLARISSA Projekt:
- CLARISSA = Conversational Language Agent for Reservoir Integrated Simulation System Analysis
- NLP-System das natürliche Sprache in ECLIPSE/OPM Flow Befehle übersetzt
- Du reviewst Code, schlägst Verbesserungen vor, lieferst Domain-Wissen

## Wichtige Regeln
1. LIES den Code sorgfältig bevor du Kritik übst
2. ZITIERE konkrete Zeilen wenn du etwas bemängelst
3. Unterscheide zwischen Query-Intents (lesen Daten) und Action-Intents (generieren ECLIPSE Code)
4. Sei KONKRET - keine vagen Empfehlungen
"""


def gitlab_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make GitLab API request."""
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/{endpoint}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    if data:
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, headers=headers, 
                                      data=json.dumps(data).encode(), method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def gitlab_fetch(path: str) -> str:
    """Fetch file content from GitLab."""
    encoded_path = path.replace("/", "%2F")
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/repository/files/{encoded_path}/raw?ref=main"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError:
        return ""


def gitlab_push(path: str, content: str, message: str) -> bool:
    """Push file to GitLab."""
    encoded_path = path.replace("/", "%2F")
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/repository/files/{encoded_path}"
    
    data = {
        "branch": "main",
        "content": content,
        "commit_message": message
    }
    
    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Try PUT (update), fall back to POST (create)
    for method in ["PUT", "POST"]:
        try:
            req = urllib.request.Request(url, headers=headers,
                                          data=json.dumps(data).encode(), method=method)
            urllib.request.urlopen(req, timeout=30)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 400 and method == "PUT":
                continue
            elif e.code == 400 and method == "POST":
                return False
    return False


def get_repo_context() -> str:
    """Build repository context from recent commits and key files."""
    context_parts = []
    
    # Recent commits
    try:
        commits = gitlab_api("repository/commits?per_page=5")
        context_parts.append("## Recent Commits")
        for c in commits[:5]:
            context_parts.append(f"- {c['short_id']}: {c['title']}")
    except:
        pass
    
    # Key files that might be referenced
    key_files = [
        "src/clarissa/agent/intents/taxonomy.json",
        "src/clarissa/agent/pipeline/intent.py",
        "src/clarissa/agent/pipeline/entities.py",
    ]
    
    for path in key_files:
        content = gitlab_fetch(path)
        if content:
            # Truncate if too long
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            context_parts.append(f"\n## {path}\n```python\n{content}\n```")
    
    return "\n".join(context_parts)


def ask_irena(question: str, context: str = "", include_repo: bool = False) -> str:
    """
    Ask IRENA (Claude) a question and get immediate response.
    
    Args:
        question: The question or task for IRENA
        context: Optional additional context (code, docs, etc.)
        include_repo: Whether to include repo context (commits, key files)
    
    Returns:
        IRENA's response text
    """
    if not ANTHROPIC_API_KEY:
        return "❌ Error: ANTHROPIC_API_KEY not set"
    
    # Build full context
    full_context = ""
    if include_repo:
        full_context += get_repo_context() + "\n\n"
    if context:
        full_context += f"## Additional Context\n{context}\n\n"
    
    user_message = question
    if full_context:
        user_message = f"{question}\n\n---\n\n{full_context}"
    
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": IRENA_SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        headers={
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY
        },
        data=json.dumps(payload).encode(),
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if "credit balance" in error_body.lower():
            return "❌ Error: Anthropic account needs credits. Go to console.anthropic.com/settings/billing"
        return f"❌ API Error {e.code}: {error_body}"
    except Exception as e:
        return f"❌ Error: {e}"


def process_handoff() -> None:
    """Process handoff file (like relay.py but Claude-to-Claude)."""
    print("📥 Checking for handoff...")
    
    handoff = gitlab_fetch("handoffs/handoff_to_irena.md")
    if not handoff:
        print("   No handoff found")
        return
    
    print(f"📬 Found handoff ({len(handoff)} chars)")
    print("📦 Building repo context...")
    
    # Get IRENA's response
    print("🤖 Asking IRENA (Claude-to-Claude)...")
    response = ask_irena(handoff, include_repo=True)
    
    # Format response
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    response_doc = f"""# 🔄 IRENA Response (Claude-to-Claude)

**Generated:** {timestamp}
**From:** IRENA (Claude Consultant)
**To:** Claude (Operator)
**Mode:** Direct API (instant)

---

{response}

---

*Generated via claude_relay.py (Anthropic API)*
"""
    
    # Push response
    print("📤 Pushing response...")
    if gitlab_push("handoffs/handoff_to_claude.md", response_doc, 
                   "feat(relay): IRENA response via Claude-to-Claude"):
        print("✅ Response written to handoffs/handoff_to_claude.md")
    else:
        print("❌ Failed to push response")
    
    # Archive original
    archive_name = f"handoffs/archive/handoff_to_irena_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    gitlab_push(archive_name, handoff, f"chore: archive handoff")
    print(f"📁 Archived to {archive_name}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Claude-to-Claude Relay")
    parser.add_argument("--question", "-q", help="Ask IRENA a direct question")
    parser.add_argument("--process", "-p", action="store_true", help="Process handoff file")
    parser.add_argument("--context", "-c", help="Additional context for question")
    parser.add_argument("--repo", "-r", action="store_true", help="Include repo context")
    
    args = parser.parse_args()
    
    if args.process:
        process_handoff()
    elif args.question:
        print("🤖 Asking IRENA...")
        response = ask_irena(args.question, context=args.context or "", include_repo=args.repo)
        print("\n" + "="*60)
        print(response)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()