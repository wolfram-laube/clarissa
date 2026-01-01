#!/usr/bin/env python3
"""
CLARISSA LLM Sync Package Generator v2.0

Generates a consolidated markdown document containing the current
repository state for sharing with LLMs that lack repository access.

Features:
- Full repository structure
- Core configuration files
- Complete ADR documentation
- Incremental diffs since last sync
- Token estimation for various LLMs
"""

import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# =============================================================================
# CONFIGURATION
# =============================================================================

GITLAB_PROJECT_ID = "77260390"
GITLAB_TOKEN = "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
DEFAULT_BRANCH = "main"

# Files to always include in full
CORE_FILES = [
    ".gitlab-ci.yml",
    "mkdocs.yml",
    "README.md",
    "CHANGELOG.md",
    "Makefile",
    ".pre-commit-config.yaml",
]

# Directories to always include completely (all files with content)
FULL_INCLUDE_DIRS = [
    "docs/adr",           # Architecture Decision Records
    "docs/architecture",  # Architecture docs
    "opmflow",            # Docker setup (Ian's work)
]

# Directories to exclude from content (structure only)
STRUCTURE_ONLY_DIRS = [
    "site_docs",
    ".idea",
    "opmflow/output",
    "conference/ijacsa-2026/figures",  # Binary PNGs
]

# File extensions to include content for (when not in FULL_INCLUDE_DIRS)
INCLUDE_EXTENSIONS = {".py", ".yml", ".yaml", ".md", ".mermaid", ".mmd", ".sh", ".tex"}

# Binary extensions to skip
SKIP_EXTENSIONS = {".png", ".pdf", ".docx", ".EGRID", ".INIT", ".UNRST", ".SMSPEC", ".DBG", ".PRT"}

# Token estimation ratios (chars per token, approximate)
TOKEN_RATIOS = {
    "claude": 3.5,      # Claude models
    "gpt-4": 4.0,       # GPT-4 / GPT-4o
    "gemini": 4.0,      # Google Gemini
    "llama": 3.8,       # Llama models
}

# Context window sizes
CONTEXT_WINDOWS = {
    "claude-opus": 200_000,
    "claude-sonnet": 200_000,
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    "gemini-pro": 1_000_000,
    "llama-3.1-405b": 128_000,
}


# =============================================================================
# GITLAB API
# =============================================================================

def gitlab_api(endpoint: str) -> dict:
    """Make GitLab API request"""
    cmd = [
        "curl", "-s",
        "--header", f"PRIVATE-TOKEN: {GITLAB_TOKEN}",
        f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/{endpoint}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout}


def get_file_content(path: str, branch: str = DEFAULT_BRANCH) -> Optional[str]:
    """Fetch file content from GitLab"""
    # Skip known binary extensions
    ext = Path(path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return None
    
    encoded_path = path.replace("/", "%2F")
    cmd = [
        "curl", "-s",
        "--header", f"PRIVATE-TOKEN: {GITLAB_TOKEN}",
        f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/repository/files/{encoded_path}/raw?ref={branch}"
    ]
    result = subprocess.run(cmd, capture_output=True)  # Don't use text=True for binary safety
    
    # Try to decode as UTF-8
    try:
        content = result.stdout.decode('utf-8')
        if content.startswith('{"error"') or content.startswith('{"message"'):
            return None
        return content
    except UnicodeDecodeError:
        # Binary file, skip
        return None


def get_recent_commits(branch: str = DEFAULT_BRANCH, n: int = 10) -> List[dict]:
    """Get recent commit history"""
    return gitlab_api(f"repository/commits?ref_name={branch}&per_page={n}")


def get_tree(branch: str = DEFAULT_BRANCH) -> List[dict]:
    """Get full repository tree"""
    return gitlab_api(f"repository/tree?ref={branch}&recursive=true&per_page=200")


def get_diff(from_ref: str, to_ref: str) -> dict:
    """Get diff between two refs"""
    return gitlab_api(f"repository/compare?from={from_ref}&to={to_ref}")


# =============================================================================
# HELPERS
# =============================================================================

def estimate_tokens(text: str) -> Dict[str, int]:
    """Estimate token count for various LLMs"""
    char_count = len(text)
    return {
        model: int(char_count / ratio)
        for model, ratio in TOKEN_RATIOS.items()
    }


def fits_in_context(text: str) -> Dict[str, str]:
    """Check if text fits in various context windows"""
    tokens = estimate_tokens(text)
    results = {}
    for model, window in CONTEXT_WINDOWS.items():
        base_model = model.split("-")[0]
        if base_model == "claude":
            est = tokens["claude"]
        elif base_model == "gpt":
            est = tokens["gpt-4"]
        elif base_model == "gemini":
            est = tokens["gemini"]
        else:
            est = tokens["llama"]
        
        pct = (est / window) * 100
        if pct < 50:
            results[model] = f"✓ {pct:.0f}% ({est:,} / {window:,})"
        elif pct < 80:
            results[model] = f"⚠ {pct:.0f}% ({est:,} / {window:,})"
        else:
            results[model] = f"✗ {pct:.0f}% ({est:,} / {window:,})"
    return results


def should_include_content(path: str) -> bool:
    """Determine if file content should be included"""
    # Check if in structure-only dirs
    for skip_dir in STRUCTURE_ONLY_DIRS:
        if path.startswith(skip_dir):
            return False
    
    # Check extension
    ext = Path(path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return False
    
    # Check if in full-include dirs
    for include_dir in FULL_INCLUDE_DIRS:
        if path.startswith(include_dir):
            return True
    
    # Otherwise check extension whitelist
    return ext in INCLUDE_EXTENSIONS


def get_file_language(path: str) -> str:
    """Get language identifier for syntax highlighting"""
    ext_map = {
        ".py": "python",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".tex": "latex",
        ".mermaid": "mermaid",
        ".mmd": "mermaid",
        ".DATA": "text",
        ".puml": "plantuml",
    }
    ext = Path(path).suffix.lower()
    return ext_map.get(ext, "text")


# =============================================================================
# SYNC PACKAGE GENERATOR
# =============================================================================

def generate_sync_package(
    output_path: str = "clarissa_sync.md",
    branch: str = DEFAULT_BRANCH,
    since_commit: Optional[str] = None,
    include_diff_content: bool = True,
    lite_mode: bool = False,
    medium_mode: bool = False,
    verbose: bool = True
) -> str:
    """Generate the sync package
    
    Args:
        lite_mode: If True, skip full directory dumps (smallest output)
        medium_mode: If True, include ADRs and arch docs but not opmflow binaries
    """
    
    tree = get_tree(branch)
    commits = get_recent_commits(branch, 10)
    
    if isinstance(tree, dict) and "error" in tree:
        print(f"Error fetching tree: {tree}")
        return ""
    
    output = []
    
    # ==========================================================================
    # HEADER
    # ==========================================================================
    output.append("# CLARISSA Repository Sync Package")
    output.append("")
    output.append("| Property | Value |")
    output.append("|----------|-------|")
    output.append(f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    output.append(f"| Branch | `{branch}` |")
    output.append(f"| Latest Commit | `{commits[0]['short_id']}` - {commits[0]['title']} |")
    output.append(f"| Total Files | {len([i for i in tree if i['type'] == 'blob'])} |")
    if since_commit:
        output.append(f"| Diff Since | `{since_commit[:8]}` |")
    
    # ==========================================================================
    # RECENT COMMITS
    # ==========================================================================
    output.append("\n## Recent Commits\n")
    for c in commits[:7]:
        date = c['created_at'][:10]
        output.append(f"- `{c['short_id']}` ({date}) {c['title']}")
    
    # ==========================================================================
    # DIRECTORY STRUCTURE
    # ==========================================================================
    output.append("\n## Repository Structure\n")
    output.append("```")
    output.append("clarissa/")
    for item in sorted(tree, key=lambda x: x['path']):
        depth = item['path'].count('/') + 1
        name = item['path'].split('/')[-1]
        prefix = "  " * depth
        marker = "/" if item['type'] == 'tree' else ""
        output.append(f"{prefix}{name}{marker}")
    output.append("```")
    
    # ==========================================================================
    # INCREMENTAL DIFF (if since_commit provided)
    # ==========================================================================
    if since_commit:
        output.append(f"\n## Changes Since `{since_commit[:8]}`\n")
        diff_data = get_diff(since_commit, branch)
        
        if 'diffs' in diff_data:
            # Summary
            new_files = [d for d in diff_data['diffs'] if d['new_file']]
            deleted_files = [d for d in diff_data['diffs'] if d['deleted_file']]
            modified_files = [d for d in diff_data['diffs'] if not d['new_file'] and not d['deleted_file']]
            
            output.append(f"**Summary:** +{len(new_files)} new, ~{len(modified_files)} modified, -{len(deleted_files)} deleted\n")
            
            output.append("### Changed Files\n")
            for d in diff_data['diffs']:
                if d['new_file']:
                    status = "+"
                elif d['deleted_file']:
                    status = "-"
                elif d['renamed_file']:
                    status = "→"
                else:
                    status = "M"
                
                rename_info = f" (← {d['old_path']})" if d['renamed_file'] else ""
                output.append(f"- `{status}` `{d['new_path']}`{rename_info}")
            
            # Include diff content for text files
            if include_diff_content:
                output.append("\n### Diff Content\n")
                for d in diff_data['diffs'][:20]:  # Limit to 20 files
                    if d['deleted_file']:
                        continue
                    ext = Path(d['new_path']).suffix.lower()
                    if ext in SKIP_EXTENSIONS:
                        continue
                    
                    output.append(f"\n#### `{d['new_path']}`\n")
                    output.append("```diff")
                    # GitLab API returns diff in d['diff']
                    if 'diff' in d and d['diff']:
                        # Truncate very long diffs
                        diff_lines = d['diff'].split('\n')
                        if len(diff_lines) > 100:
                            output.append('\n'.join(diff_lines[:100]))
                            output.append(f"\n... ({len(diff_lines) - 100} more lines)")
                        else:
                            output.append(d['diff'])
                    output.append("```")
    
    # ==========================================================================
    # CORE CONFIGURATION FILES
    # ==========================================================================
    output.append("\n## Core Configuration Files\n")
    for filepath in CORE_FILES:
        content = get_file_content(filepath, branch)
        if content:
            lang = get_file_language(filepath)
            output.append(f"\n### `{filepath}`\n")
            output.append(f"```{lang}")
            output.append(content.rstrip())
            output.append("```")
    
    # ==========================================================================
    # FULL INCLUDE DIRECTORIES (skip in lite mode, selective in medium mode)
    # ==========================================================================
    if lite_mode:
        include_dirs = []
    elif medium_mode:
        # Medium: ADRs and architecture docs, but not opmflow (too large)
        include_dirs = ["docs/adr", "docs/architecture"]
    else:
        # Full: everything
        include_dirs = FULL_INCLUDE_DIRS
    
    for include_dir in include_dirs:
            dir_files = [
                item for item in tree
                if item['path'].startswith(include_dir) and item['type'] == 'blob'
            ]
            
            if dir_files:
                output.append(f"\n## Directory: `{include_dir}/`\n")
                
                for item in sorted(dir_files, key=lambda x: x['path']):
                    filepath = item['path']
                    ext = Path(filepath).suffix.lower()
                    
                    if ext in SKIP_EXTENSIONS:
                        output.append(f"\n### `{filepath}` *(binary, skipped)*\n")
                        continue
                    
                    content = get_file_content(filepath, branch)
                    if content:
                        lang = get_file_language(filepath)
                        output.append(f"\n### `{filepath}`\n")
                        output.append(f"```{lang}")
                        output.append(content.rstrip())
                        output.append("```")
    
    # ==========================================================================
    # TOKEN ESTIMATION
    # ==========================================================================
    result = "\n".join(output)
    
    output.append("\n---\n")
    output.append("## Token Estimation\n")
    output.append(f"**Total Characters:** {len(result):,}\n")
    output.append("| Model | Fit Status |")
    output.append("|-------|------------|")
    
    fit_status = fits_in_context(result)
    for model, status in fit_status.items():
        output.append(f"| {model} | {status} |")
    
    # Rebuild with token section
    result = "\n".join(output)
    
    # ==========================================================================
    # WRITE OUTPUT
    # ==========================================================================
    with open(output_path, 'w') as f:
        f.write(result)
    
    if verbose:
        print(f"✓ Sync package generated: {output_path}")
        print(f"  Characters: {len(result):,}")
        tokens = estimate_tokens(result)
        print(f"  Est. tokens: ~{tokens['claude']:,} (Claude) / ~{tokens['gpt-4']:,} (GPT-4)")
        print()
        print("  Context window fit:")
        for model, status in fit_status.items():
            print(f"    {model}: {status}")
    
    return output_path


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate CLARISSA LLM Sync Package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full sync package
  %(prog)s --since abc123           # Include diff since commit
  %(prog)s --branch feature/xyz     # Sync specific branch
  %(prog)s --output sync.md         # Custom output file
  %(prog)s --no-diff-content        # Omit diff content (smaller file)
        """
    )
    
    parser.add_argument(
        "--since", "-s",
        help="Include diff since this commit hash"
    )
    parser.add_argument(
        "--branch", "-b",
        default=DEFAULT_BRANCH,
        help=f"Branch to sync (default: {DEFAULT_BRANCH})"
    )
    parser.add_argument(
        "--output", "-o",
        default="clarissa_sync.md",
        help="Output file path"
    )
    parser.add_argument(
        "--no-diff-content",
        action="store_true",
        help="Don't include actual diff content (just file list)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--lite", "-l",
        action="store_true",
        help="Lite mode: only core files, no full directory dumps"
    )
    parser.add_argument(
        "--medium", "-m",
        action="store_true",
        help="Medium mode: core files + ADRs + architecture docs (fits in Claude)"
    )
    
    args = parser.parse_args()
    
    generate_sync_package(
        output_path=args.output,
        branch=args.branch,
        since_commit=args.since,
        include_diff_content=not args.no_diff_content,
        lite_mode=args.lite,
        medium_mode=args.medium,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
