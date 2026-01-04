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
    print("🤖 Calling OpenAI API...")
    response = call_openai_api(system_prompt, handoff_content, dry_run)
    
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