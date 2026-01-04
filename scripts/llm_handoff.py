#!/usr/bin/env python3
"""LLM Handoff Generator - Sync between Claude and ChatGPT.

Creates structured handoff documents for transferring context between
different LLM sessions working on the same project.

Usage:
    python llm_handoff.py --from claude --to chatgpt
    python llm_handoff.py --from chatgpt --to claude --input handoff.md
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def get_git_info() -> dict:
    """Get current git state."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Recent commits
        log = subprocess.check_output(
            ["git", "log", "--oneline", "-5"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return {
            "branch": branch,
            "commit": commit,
            "recent_commits": log.split("\n")
        }
    except Exception:
        return {"branch": "unknown", "commit": "unknown", "recent_commits": []}


def get_open_issues(gitlab_token: str, project_id: str) -> list:
    """Fetch open issues from GitLab."""
    try:
        import urllib.request
        url = f"https://gitlab.com/api/v4/projects/{project_id}/issues?state=opened"
        req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": gitlab_token})
        with urllib.request.urlopen(req, timeout=10) as resp:
            issues = json.loads(resp.read().decode())
            return [
                {
                    "id": i["iid"],
                    "title": i["title"],
                    "labels": [l for l in i.get("labels", []) if "priority" in l],
                }
                for i in issues[:10]
            ]
    except Exception as e:
        return [{"error": str(e)}]


def get_recent_changes(gitlab_token: str, project_id: str) -> list:
    """Fetch recent file changes."""
    try:
        import urllib.request
        url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=5"
        req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": gitlab_token})
        with urllib.request.urlopen(req, timeout=10) as resp:
            commits = json.loads(resp.read().decode())
            return [
                {
                    "sha": c["short_id"],
                    "message": c["title"],
                    "date": c["created_at"][:10],
                }
                for c in commits
            ]
    except Exception:
        return []


def get_pipeline_status(gitlab_token: str, project_id: str) -> str:
    """Get latest pipeline status."""
    try:
        import urllib.request
        url = f"https://gitlab.com/api/v4/projects/{project_id}/pipelines?per_page=1"
        req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": gitlab_token})
        with urllib.request.urlopen(req, timeout=10) as resp:
            pipelines = json.loads(resp.read().decode())
            if pipelines:
                p = pipelines[0]
                return f"{p['status']} (#{p['id']})"
            return "unknown"
    except Exception:
        return "unknown"


HANDOFF_TEMPLATE = """# 🔄 LLM Handoff Document

**Generated:** {timestamp}
**From:** {from_llm}
**To:** {to_llm}
**Project:** CLARISSA (IRENA)

---

## 📊 Project State

**Git Branch:** `{branch}`
**Latest Commit:** `{commit}`
**Pipeline Status:** {pipeline_status}

### Recent Commits
{recent_commits}

---

## 📋 Open Issues ({issue_count})

{issues}

---

## 🎯 Current Focus

{current_focus}

---

## 💬 Context for {to_llm}

{context}

---

## ❓ Questions / Review Requests

{questions}

---

## 📎 Relevant Files

{files}

---

## 🔗 Links

- GitLab: https://gitlab.com/wolfram_laube/blauweiss_llc/irena
- Docs: https://wolfram_laube.gitlab.io/blauweiss_llc/irena/

---

*Copy this entire document to {to_llm} for context transfer.*
"""


def generate_handoff(
    from_llm: str,
    to_llm: str,
    current_focus: str = "",
    context: str = "",
    questions: str = "",
    files: str = "",
) -> str:
    """Generate a handoff document."""
    
    gitlab_token = os.environ.get(
        "GITLAB_TOKEN", 
        "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
    )
    project_id = "77260390"
    
    git_info = get_git_info()
    issues = get_open_issues(gitlab_token, project_id)
    recent = get_recent_changes(gitlab_token, project_id)
    pipeline = get_pipeline_status(gitlab_token, project_id)
    
    # Format commits
    commits_md = "\n".join(
        f"- `{c['sha']}` {c['message']}" 
        for c in recent
    ) if recent else "- (unable to fetch)"
    
    # Format issues
    if issues and "error" not in issues[0]:
        issues_md = "\n".join(
            f"- **#{i['id']}** {i['title']}"
            for i in issues
        )
    else:
        issues_md = "- (unable to fetch)"
    
    return HANDOFF_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        from_llm=from_llm,
        to_llm=to_llm,
        branch=git_info["branch"],
        commit=git_info["commit"],
        pipeline_status=pipeline,
        recent_commits=commits_md,
        issue_count=len(issues) if issues else "?",
        issues=issues_md,
        current_focus=current_focus or "(please fill in)",
        context=context or "(please fill in)",
        questions=questions or "(please fill in)",
        files=files or "(please fill in)",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate LLM handoff documents for Claude ↔ ChatGPT sync"
    )
    parser.add_argument(
        "--from", dest="from_llm", default="Claude",
        help="Source LLM (default: Claude)"
    )
    parser.add_argument(
        "--to", dest="to_llm", default="ChatGPT",
        help="Target LLM (default: ChatGPT)"
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
        "--files", default="",
        help="Relevant files to highlight"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    handoff = generate_handoff(
        from_llm=args.from_llm,
        to_llm=args.to_llm,
        current_focus=args.focus,
        context=args.context,
        questions=args.questions,
        files=args.files,
    )
    
    if args.output:
        Path(args.output).write_text(handoff)
        print(f"✅ Handoff saved to: {args.output}")
    else:
        print(handoff)


if __name__ == "__main__":
    main()