#!/usr/bin/env python3
"""LLM Handoff Generator - Sync between Claude and ChatGPT.

Creates structured handoff documents for transferring context between
different LLM sessions working on the same project.

Usage:
    # Basic handoff
    python llm_handoff.py --from Claude --to ChatGPT
    
    # With code and copy to clipboard
    python llm_handoff.py --include-code --copy
    
    # Full options
    python llm_handoff.py \\
        --from "Claude (Operator)" \\
        --to "ChatGPT IRENA (Consultant)" \\
        --focus "NLP Pipeline done" \\
        --questions "Review intent categories" \\
        --include-code \\
        --copy
"""

import argparse
import json
import os
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Configuration
GITLAB_PROJECT_ID = "77260390"
GITLAB_TOKEN_ENV = "GITLAB_TOKEN"
GITLAB_TOKEN_DEFAULT = "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"

# Files to include when --include-code is used
CODE_FILES = [
    "src/clarissa/agent/intents/taxonomy.json",
    "src/clarissa/agent/pipeline/intent.py",
    "src/clarissa/agent/pipeline/entities.py",
    "src/clarissa/agent/pipeline/validation.py",
]


def get_gitlab_token() -> str:
    """Get GitLab token from environment or default."""
    return os.environ.get(GITLAB_TOKEN_ENV, GITLAB_TOKEN_DEFAULT)


def gitlab_api(endpoint: str) -> dict | list | str | None:
    """Make GitLab API request."""
    token = get_gitlab_token()
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/{endpoint}"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": token})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
    except urllib.error.URLError as e:
        print(f"⚠️  GitLab API error: {e}")
        return None


def get_file_content(path: str) -> str | None:
    """Fetch file content from GitLab."""
    encoded_path = path.replace("/", "%2F")
    return gitlab_api(f"repository/files/{encoded_path}/raw?ref=main")


def get_open_issues() -> list[dict]:
    """Fetch open issues from GitLab."""
    issues = gitlab_api("issues?state=opened&per_page=15")
    if not issues or isinstance(issues, str):
        return []
    return [
        {
            "id": i["iid"],
            "title": i["title"],
            "labels": [l for l in i.get("labels", []) if "priority" in l],
        }
        for i in issues
    ]


def get_recent_commits() -> list[dict]:
    """Fetch recent commits."""
    commits = gitlab_api("repository/commits?per_page=5")
    if not commits or isinstance(commits, str):
        return []
    return [
        {
            "sha": c["short_id"],
            "message": c["title"],
            "date": c["created_at"][:10],
        }
        for c in commits
    ]


def get_pipeline_status() -> str:
    """Get latest pipeline status."""
    pipelines = gitlab_api("pipelines?per_page=1")
    if not pipelines or isinstance(pipelines, str):
        return "unknown"
    if pipelines:
        p = pipelines[0]
        icon = {"success": "✅", "failed": "❌", "running": "🔄"}.get(p["status"], "?")
        return f"{icon} {p['status']} (#{p['id']})"
    return "unknown"


def copy_to_clipboard(text: str) -> bool:
    """Try to copy text to clipboard."""
    # Try pyperclip first
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass
    
    # Try pbcopy (macOS)
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    # Try xclip (Linux)
    try:
        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    # Try xsel (Linux alternative)
    try:
        process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    # Try powershell clip (Windows)
    try:
        process = subprocess.Popen(['powershell', '-command', 'Set-Clipboard'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    return False


def generate_handoff(
    from_llm: str,
    to_llm: str,
    current_focus: str = "",
    context: str = "",
    questions: str = "",
    include_code: bool = False,
) -> str:
    """Generate a handoff document."""
    
    # Fetch project state
    issues = get_open_issues()
    commits = get_recent_commits()
    pipeline = get_pipeline_status()
    
    # Format sections
    commits_md = "\n".join(
        f"- `{c['sha']}` {c['message']}" for c in commits
    ) if commits else "- (unable to fetch)"
    
    issues_md = "\n".join(
        f"- **#{i['id']}** {i['title']}" for i in issues
    ) if issues else "- (unable to fetch)"
    
    # Build document
    doc = f"""# 🔄 LLM Handoff Document

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**From:** {from_llm}
**To:** {to_llm}
**Project:** CLARISSA (IRENA)

---

## 📊 Project State

**Pipeline Status:** {pipeline}

### Recent Commits
{commits_md}

---

## 📋 Open Issues ({len(issues)})

{issues_md}

---

## 🎯 Current Focus

{current_focus or "(not specified)"}

---

## 💬 Context

{context or "(not specified)"}

---

## ❓ Questions / Review Requests

{questions or "(not specified)"}

"""
    
    # Add code if requested
    if include_code:
        doc += """---

## 📁 Code for Review

"""
        for filepath in CODE_FILES:
            content = get_file_content(filepath)
            if content:
                filename = filepath.split("/")[-1]
                ext = filename.split(".")[-1]
                
                # Truncate very long files
                lines = content.split("\n")
                if len(lines) > 200:
                    content = "\n".join(lines[:100]) + "\n\n# ... (truncated) ...\n\n" + "\n".join(lines[-50:])
                
                doc += f"""### `{filepath}`

```{ext}
{content}
```

"""
            else:
                doc += f"### `{filepath}`\n\n(unable to fetch)\n\n"
    
    doc += """---

## 🔗 Links

- **GitLab:** https://gitlab.com/wolfram_laube/blauweiss_llc/irena
- **Docs:** https://wolfram_laube.gitlab.io/blauweiss_llc/irena/

---

*Paste this into ChatGPT for context transfer.*
"""
    
    return doc


def main():
    parser = argparse.ArgumentParser(
        description="Generate LLM handoff documents for Claude ↔ ChatGPT sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --copy
      Generate basic handoff and copy to clipboard
  
  %(prog)s --include-code --copy
      Include code files and copy to clipboard
  
  %(prog)s --focus "NLP done" --questions "Review intents" --include-code -o handoff.md
      Full handoff with custom focus, questions, code, saved to file
"""
    )
    parser.add_argument(
        "--from", dest="from_llm", default="Claude (Operator)",
        help="Source LLM (default: Claude (Operator))"
    )
    parser.add_argument(
        "--to", dest="to_llm", default="ChatGPT IRENA (Consultant)",
        help="Target LLM (default: ChatGPT IRENA (Consultant))"
    )
    parser.add_argument(
        "--focus", default="",
        help="Current focus/task description"
    )
    parser.add_argument(
        "--context", default="",
        help="Additional context for target LLM"
    )
    parser.add_argument(
        "--questions", default="",
        help="Questions or review requests"
    )
    parser.add_argument(
        "--include-code", action="store_true",
        help="Include key code files from GitLab"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--copy", "-c", action="store_true",
        help="Copy to clipboard"
    )
    
    args = parser.parse_args()
    
    print("🔄 Generating handoff...")
    
    handoff = generate_handoff(
        from_llm=args.from_llm,
        to_llm=args.to_llm,
        current_focus=args.focus,
        context=args.context,
        questions=args.questions,
        include_code=args.include_code,
    )
    
    if args.output:
        Path(args.output).write_text(handoff)
        print(f"✅ Saved to: {args.output}")
    
    if args.copy:
        if copy_to_clipboard(handoff):
            print("📋 Copied to clipboard!")
            print("   → Open ChatGPT and press Cmd+V (Mac) or Ctrl+V (Win/Linux)")
        else:
            print("⚠️  Could not copy to clipboard.")
            print("   Install pyperclip: pip install pyperclip")
            print("   Or use: --output handoff.md")
    
    if not args.output and not args.copy:
        print(handoff)
    
    print(f"\n📊 Summary: {len(handoff)} chars, {len(handoff.split(chr(10)))} lines")


if __name__ == "__main__":
    main()