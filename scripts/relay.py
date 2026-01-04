#!/usr/bin/env python3
"""LLM Relay - Asynchronous communication between Claude and ChatGPT.

This script enables asynchronous communication between Claude (Operator)
and ChatGPT/IRENA (Consultant) via a shared Google Drive folder.

Architecture:
    Claude writes → handoff_to_irena.md → relay.py reads
                                              ↓
                                         OpenAI API
                                              ↓
    Claude reads  ← handoff_to_claude.md ← relay.py writes

Usage:
    # Process pending handoff from Claude
    python relay.py --process
    
    # Watch for new handoffs (polling mode)
    python relay.py --watch --interval 60
    
    # Dry run (don't call API)
    python relay.py --process --dry-run

Requirements:
    pip install openai google-api-python-client google-auth-oauthlib

Environment Variables:
    OPENAI_API_KEY     - OpenAI API key
    GOOGLE_DRIVE_FOLDER_ID - Shared folder ID (optional, uses default)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Configuration
GITLAB_PROJECT_ID = "77260390"
GITLAB_TOKEN = os.environ.get(
    "GITLAB_TOKEN",
    "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
)

# Knowledge base files in GitLab
KNOWLEDGE_FILES = [
    "docs/llm_knowledge/irena_system_prompt.md",
    "docs/llm_knowledge/clarissa_context.md",
    "docs/llm_knowledge/eclipse_reference.md",
    "docs/llm_knowledge/intent_taxonomy.md",
]

# Local paths
HANDOFF_DIR = Path("handoffs")
HANDOFF_TO_IRENA = HANDOFF_DIR / "handoff_to_irena.md"
HANDOFF_TO_CLAUDE = HANDOFF_DIR / "handoff_to_claude.md"


def gitlab_fetch(path: str) -> str | None:
    """Fetch file content from GitLab."""
    encoded_path = path.replace("/", "%2F")
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/repository/files/{encoded_path}/raw?ref=main"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode()
    except urllib.error.URLError as e:
        print(f"⚠️  Failed to fetch {path}: {e}")
        return None



def get_recent_commits(n: int = 5) -> list[dict]:
    """Fetch recent commits with diffs."""
    commits = gitlab_api(f"repository/commits?per_page={n}")
    if not commits or isinstance(commits, str):
        return []
    
    result = []
    for c in commits:
        commit_detail = gitlab_api(f"repository/commits/{c['id']}/diff")
        result.append({
            "sha": c["short_id"],
            "message": c["title"],
            "date": c["created_at"][:10],
            "author": c.get("author_name", "unknown"),
            "diff_summary": summarize_diff(commit_detail) if commit_detail else ""
        })
    return result


def summarize_diff(diff: list) -> str:
    """Summarize a diff into readable format."""
    if not diff:
        return ""
    
    summary = []
    for file_diff in diff[:10]:  # Limit to 10 files
        path = file_diff.get("new_path", file_diff.get("old_path", "unknown"))
        
        # Count additions/deletions
        diff_text = file_diff.get("diff", "")
        additions = diff_text.count("\n+") - diff_text.count("\n+++")
        deletions = diff_text.count("\n-") - diff_text.count("\n---")
        
        summary.append(f"  {path}: +{additions}/-{deletions}")
    
    return "\n".join(summary)


def get_file_contents(paths: list[str], max_lines: int = 150) -> dict[str, str]:
    """Fetch multiple file contents from GitLab."""
    result = {}
    for path in paths:
        content = gitlab_fetch(path)
        if content:
            lines = content.split("\n")
            if len(lines) > max_lines:
                content = "\n".join(lines[:80]) + "\n\n# ... truncated ...\n\n" + "\n".join(lines[-40:])
            result[path] = content
    return result


def gitlab_api(endpoint: str) -> dict | list | str | None:
    """Make GitLab API request returning JSON."""
    token = GITLAB_TOKEN
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/{endpoint}"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": token})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"⚠️  GitLab API error: {e}")
        return None


def build_repo_context(include_diff: bool = True, include_files: list[str] = None) -> str:
    """Build repository context for the handoff."""
    context_parts = []
    
    # Recent commits with diffs
    if include_diff:
        commits = get_recent_commits(5)
        if commits:
            context_parts.append("## 📝 Recent Commits\n")
            for c in commits:
                context_parts.append(f"### `{c['sha']}` - {c['message']} ({c['date']})")
                if c['diff_summary']:
                    context_parts.append(f"```\n{c['diff_summary']}\n```")
            context_parts.append("")
    
    # Specific file contents
    if include_files:
        files = get_file_contents(include_files)
        if files:
            context_parts.append("## 📁 Relevant Code\n")
            for path, content in files.items():
                ext = path.split(".")[-1]
                context_parts.append(f"### `{path}`\n```{ext}\n{content}\n```\n")
    
    return "\n".join(context_parts)


def load_knowledge_base() -> str:
    """Load all knowledge base files from GitLab."""
    knowledge = []
    for path in KNOWLEDGE_FILES:
        content = gitlab_fetch(path)
        if content:
            knowledge.append(f"# FILE: {path}\n\n{content}")
    return "\n\n---\n\n".join(knowledge)


def build_system_prompt(knowledge: str) -> str:
    """Build the system prompt for IRENA."""
    return f"""Du bist IRENA (Intelligent Reservoir Engineering Natural-language Assistant).

{knowledge}

---

WICHTIG: 
- Antworte auf Deutsch
- Sei konkret und umsetzbar
- Claude wird deine Antworten implementieren
- Formatiere Empfehlungen so, dass sie direkt als Issues/Code verwendbar sind
"""


def call_openai_api(system_prompt: str, user_message: str, dry_run: bool = False) -> str:
    """Call OpenAI API with IRENA persona."""
    if dry_run:
        return "[DRY RUN] Would call OpenAI API with:\n" + user_message[:500] + "..."
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "ERROR: OPENAI_API_KEY not set"
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4000,
            temperature=0.7,
        )
        
        return response.choices[0].message.content
        
    except ImportError:
        return "ERROR: openai package not installed. Run: pip install openai"
    except Exception as e:
        return f"ERROR: OpenAI API call failed: {e}"


def process_handoff(dry_run: bool = False) -> bool:
    """Process a pending handoff from Claude."""
    
    # Check for pending handoff
    if not HANDOFF_TO_IRENA.exists():
        print("ℹ️  No pending handoff found")
        return False
    
    print(f"📥 Found handoff: {HANDOFF_TO_IRENA}")
    handoff_content = HANDOFF_TO_IRENA.read_text()
    
    # Load knowledge base
    print("📚 Loading knowledge base from GitLab...")
    knowledge = load_knowledge_base()
    
    if not knowledge:
        print("⚠️  Could not load knowledge base")
        return False
    
    print(f"   Loaded {len(knowledge)} chars of knowledge")
    
    # Build prompt
    system_prompt = build_system_prompt(knowledge)
    
    # Call API
    # Add repo context to handoff
    print("📦 Building repository context...")
    
    # Check if handoff requests specific files
    include_files = []
    if "taxonomy.json" in handoff_content.lower():
        include_files.append("src/clarissa/agent/intents/taxonomy.json")
    if "intent.py" in handoff_content.lower() or "intent" in handoff_content.lower():
        include_files.append("src/clarissa/agent/pipeline/intent.py")
    if "entities.py" in handoff_content.lower() or "entity" in handoff_content.lower():
        include_files.append("src/clarissa/agent/pipeline/entities.py")
    
    repo_context = build_repo_context(
        include_diff=True,
        include_files=include_files if include_files else None
    )
    
    # Combine handoff with repo context
    full_handoff = handoff_content + "\n\n---\n\n# Repository Context\n\n" + repo_context
    
    print("🤖 Calling OpenAI API...")
    response = call_openai_api(system_prompt, full_handoff, dry_run)
    
    if response.startswith("ERROR"):
        print(f"❌ {response}")
        return False
    
    # Write response
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    response_doc = f"""# 🔄 IRENA Response

**Generated:** {timestamp}
**From:** IRENA (Consultant)
**To:** Claude (Operator)

---

{response}

---

*Generated via relay.py from OpenAI API*
"""
    
    HANDOFF_TO_CLAUDE.write_text(response_doc)
    print(f"✅ Response written to: {HANDOFF_TO_CLAUDE}")
    
    # Archive processed handoff
    archive_dir = HANDOFF_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    archive_name = f"handoff_to_irena_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    HANDOFF_TO_IRENA.rename(archive_dir / archive_name)
    print(f"📁 Archived to: {archive_dir / archive_name}")
    
    return True


def watch_mode(interval: int, dry_run: bool = False):
    """Watch for new handoffs and process them."""
    print(f"👀 Watching for handoffs every {interval}s...")
    print("   Press Ctrl+C to stop")
    
    try:
        while True:
            if HANDOFF_TO_IRENA.exists():
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New handoff detected!")
                process_handoff(dry_run)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Stopped watching")


def setup():
    """Create necessary directories."""
    HANDOFF_DIR.mkdir(exist_ok=True)
    (HANDOFF_DIR / "archive").mkdir(exist_ok=True)
    print(f"✅ Created handoff directory: {HANDOFF_DIR}")
    print(f"\nTo use:")
    print(f"  1. Claude writes handoff to: {HANDOFF_TO_IRENA}")
    print(f"  2. Run: python relay.py --process")
    print(f"  3. Read response from: {HANDOFF_TO_CLAUDE}")


def main():
    parser = argparse.ArgumentParser(
        description="LLM Relay - Claude ↔ ChatGPT communication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --setup
      Create handoff directories
  
  %(prog)s --process
      Process pending handoff
  
  %(prog)s --watch --interval 30
      Poll for new handoffs every 30 seconds
  
  %(prog)s --process --dry-run
      Test without calling API
"""
    )
    parser.add_argument("--setup", action="store_true", help="Create directories")
    parser.add_argument("--process", action="store_true", help="Process pending handoff")
    parser.add_argument("--watch", action="store_true", help="Watch for new handoffs")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Don't call API")
    
    args = parser.parse_args()
    
    if args.setup:
        setup()
    elif args.process:
        HANDOFF_DIR.mkdir(exist_ok=True)
        process_handoff(args.dry_run)
    elif args.watch:
        HANDOFF_DIR.mkdir(exist_ok=True)
        watch_mode(args.interval, args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()