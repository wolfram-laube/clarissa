#!/usr/bin/env python3
"""
Generic Project Rename Script

A parameterized script for renaming projects across all files, directories,
and content. Configure the OLD/NEW sections below and run.

Usage:
    python3 rename_project.py [--dry-run]
    
Options:
    --dry-run    Show what would be changed without making changes
"""

import requests
import base64
import sys
from pathlib import Path
from typing import Optional

# =============================================================================
# CONFIGURATION - Edit these values for your rename
# =============================================================================

# GitLab Configuration
GITLAB_TOKEN = "glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt"
GITLAB_PROJECT_ID = "77260390"
GITLAB_BRANCH = "feature/orsa-v30-synthetic-talk"

# Project Names
OLD_NAME = {
    "upper": "CLARISSA",                    # CLARISSA
    "lower": "clarissa",                    # clarissa  
    "title": "Clarissa",                    # Clarissa
    "full": "Conversational Language Agent for Reservoir Integrated Simulation System Analysis",
}

NEW_NAME = {
    "upper": "CLARISSA",                    # Change to new name
    "lower": "clarissa",                    # Change to new name
    "title": "Clarissa",                    # Change to new name
    "full": "Conversational Language Agent for Reservoir Integrated Simulation System Analysis",
}

# Environment variable prefix (e.g., CLARISSA_AUTO_APPROVE or just AUTO_APPROVE)
OLD_ENV_PREFIX = ""   # Empty = no prefix (AUTO_APPROVE)
NEW_ENV_PREFIX = ""   # Empty = no prefix (AUTO_APPROVE)

# =============================================================================
# END CONFIGURATION
# =============================================================================

# GitLab API setup
BASE_URL = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/repository"
headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}

# Binary file extensions (don't do text replacement)
BINARY_EXTENSIONS = {'.png', '.pdf', '.docx', '.jpg', '.jpeg', '.gif', '.ico', 
                     '.woff', '.woff2', '.ttf', '.eot', '.zip', '.tar', '.gz'}


def build_replacements() -> list:
    """Build the list of text replacements from configuration"""
    replacements = []
    
    # Only add replacements if old != new
    if OLD_NAME["upper"] != NEW_NAME["upper"]:
        old_u, new_u = OLD_NAME["upper"], NEW_NAME["upper"]
        old_l, new_l = OLD_NAME["lower"], NEW_NAME["lower"]
        old_t, new_t = OLD_NAME["title"], NEW_NAME["title"]
        old_f, new_f = OLD_NAME["full"], NEW_NAME["full"]
        
        # Full name with acronym
        replacements.extend([
            (f"{old_f} ({old_u})", f"{new_f} ({new_u})"),
            (f"{old_u} – {old_f}", f"{new_u} – {new_f}"),
            (old_f, new_f),
        ])
        
        # Compound terms (longer patterns first)
        replacements.extend([
            (f"{old_u}Agent", f"{new_u}Agent"),
            (f"{old_u}-Native", f"{new_u}-Native"),
            (f"{old_u}-native", f"{new_u}-native"),
            (f"{old_u}/RL", f"{new_u}/RL"),
            (f"{old_u}/LLM", f"{new_u}/LLM"),
            (f"{old_u}/GOV", f"{new_u}/GOV"),
            (f"[{old_u}]", f"[{new_u}]"),
            (f"M{old_u}", f"M{new_u}"),  # Master-variant
            (f"F{old_u}", f"F{new_u}"),  # Field-variant
        ])
        
        # Standalone acronym
        replacements.append((old_u, new_u))
        
        # Lowercase variants
        replacements.extend([
            (f"{old_l}_kernel", f"{new_l}_kernel"),
            (f"{old_l}-", f"{new_l}-"),
            (f"{old_l}/", f"{new_l}/"),
            (f"{old_l}.", f"{new_l}."),
            (f"{old_l})", f"{new_l})"),
            (f"{old_l}`", f"{new_l}`"),
            (f"{old_l} ", f"{new_l} "),
            (f"'{old_l}'", f"'{new_l}'"),
            (f'"{old_l}"', f'"{new_l}"'),
            (f"-m {old_l}", f"-m {new_l}"),
            (f"import {old_l}", f"import {new_l}"),
            (f"from {old_l}", f"from {new_l}"),
            (f"[{old_l}]", f"[{new_l}]"),
            (f"[{old_l}<", f"[{new_l}<"),  # [clarissa<path>
        ])
        
        # Title case
        replacements.append((old_t, new_t))
    
    # Environment variable prefix
    if OLD_ENV_PREFIX != NEW_ENV_PREFIX:
        if OLD_ENV_PREFIX and NEW_ENV_PREFIX:
            replacements.append((f"{OLD_ENV_PREFIX}_", f"{NEW_ENV_PREFIX}_"))
        elif OLD_ENV_PREFIX and not NEW_ENV_PREFIX:
            # Remove prefix
            replacements.append((f"{OLD_ENV_PREFIX}_AUTO_APPROVE", "AUTO_APPROVE"))
        elif not OLD_ENV_PREFIX and NEW_ENV_PREFIX:
            # Add prefix
            replacements.append(("AUTO_APPROVE", f"{NEW_ENV_PREFIX}_AUTO_APPROVE"))
    
    return replacements


def build_path_renames() -> dict:
    """Build the dictionary of path renames from configuration"""
    renames = {}
    
    if OLD_NAME["lower"] != NEW_NAME["lower"]:
        old_l, new_l = OLD_NAME["lower"], NEW_NAME["lower"]
        old_u, new_u = OLD_NAME["upper"], NEW_NAME["upper"]
        
        # Source directories
        renames[f"src/{old_l}"] = f"src/{new_l}"
        renames[f"src/{old_l}_kernel"] = f"src/{new_l}_kernel"
        
        # Conference files pattern
        conference_files = [
            "Paper_IJACSA.tex", "Paper_IJACSA.pdf", "Paper_IJACSA.docx",
            "Figure1_Architecture.png", "Figure1_Architecture.mermaid",
            "Figure2_NLP_Pipeline.png", "Figure2_NLP_Pipeline.mermaid",
            "Figure3_DataMesh.png", "Figure3_DataMesh.mermaid",
            "Figure4_Communication.png", "Figure4_Communication.mermaid",
            "Abstract_CFP.pdf", "Architecture_Summary_Detailed.pdf",
        ]
        
        for f in conference_files:
            if "Figure" in f or "Paper" in f:
                old_path = f"conference/ijacsa-2026/figures/{old_u}_{f}" if "Figure" in f else f"conference/ijacsa-2026/{old_u}_{f}"
                new_path = f"conference/ijacsa-2026/figures/{new_u}_{f}" if "Figure" in f else f"conference/ijacsa-2026/{new_u}_{f}"
            else:
                old_path = f"conference/ijacsa-2026/supplementary/{old_u}_{f}"
                new_path = f"conference/ijacsa-2026/supplementary/{new_u}_{f}"
            renames[old_path] = new_path
    
    return renames


def get_all_files() -> list:
    """Get all files from the repository"""
    files = []
    page = 1
    while True:
        resp = requests.get(
            f"{BASE_URL}/tree",
            params={"ref": GITLAB_BRANCH, "recursive": "true", "per_page": 100, "page": page},
            headers=headers
        )
        data = resp.json()
        if not data:
            break
        files.extend([f for f in data if f['type'] == 'blob'])
        page += 1
    return files


def get_file_content(path: str) -> Optional[bytes]:
    """Download file content"""
    encoded_path = requests.utils.quote(path, safe='')
    resp = requests.get(
        f"{BASE_URL}/files/{encoded_path}/raw",
        params={"ref": GITLAB_BRANCH},
        headers=headers
    )
    if resp.status_code == 200:
        return resp.content
    return None


def is_binary(path: str) -> bool:
    """Check if file is binary based on extension"""
    return Path(path).suffix.lower() in BINARY_EXTENSIONS


def replace_text(content: str, replacements: list) -> str:
    """Apply all text replacements"""
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def get_new_path(old_path: str, path_renames: dict) -> str:
    """Get the new path for a file (handles directory renames)"""
    # Check direct renames first
    if old_path in path_renames:
        return path_renames[old_path]
    
    # Check directory renames
    for old_dir, new_dir in path_renames.items():
        if old_path.startswith(old_dir + "/"):
            return new_dir + old_path[len(old_dir):]
    
    return old_path


def create_commit_actions(files_data: list) -> list:
    """Create GitLab commit actions for all changes"""
    actions = []
    
    for file_info in files_data:
        old_path = file_info['path']
        new_path = file_info['new_path']
        content = file_info['content']
        is_bin = file_info['is_binary']
        
        if old_path != new_path:
            # File is being moved/renamed
            actions.append({"action": "delete", "file_path": old_path})
            actions.append({
                "action": "create",
                "file_path": new_path,
                "content": base64.b64encode(content).decode() if is_bin else content,
                "encoding": "base64" if is_bin else "text"
            })
        elif not is_bin and file_info.get('modified'):
            # Content was modified (text file only)
            actions.append({
                "action": "update",
                "file_path": old_path,
                "content": content,
                "encoding": "text"
            })
    
    return actions


def commit_changes(actions: list, message: str) -> bool:
    """Commit changes using GitLab API"""
    if not actions:
        print("No actions to commit")
        return True
    
    BATCH_SIZE = 50
    
    for i in range(0, len(actions), BATCH_SIZE):
        batch = actions[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(actions) + BATCH_SIZE - 1) // BATCH_SIZE
        
        data = {
            "branch": GITLAB_BRANCH,
            "commit_message": f"{message} (batch {batch_num}/{total_batches})" if total_batches > 1 else message,
            "actions": batch
        }
        
        resp = requests.post(f"{BASE_URL}/commits", headers=headers, json=data)
        
        if resp.status_code not in [200, 201]:
            print(f"✗ Commit failed: {resp.status_code}")
            print(resp.text[:500])
            return False
        
        print(f"✓ Committed batch {batch_num}/{total_batches}")
    
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("Generic Project Rename Script")
    print("=" * 60)
    print()
    print(f"From: {OLD_NAME['upper']} ({OLD_NAME['full']})")
    print(f"To:   {NEW_NAME['upper']} ({NEW_NAME['full']})")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    # Build replacement rules
    replacements = build_replacements()
    path_renames = build_path_renames()
    
    if not replacements and not path_renames:
        print("⚠️  No changes configured (OLD_NAME == NEW_NAME)")
        return True
    
    print(f"📋 Text replacements: {len(replacements)}")
    print(f"📋 Path renames: {len(path_renames)}")
    print()
    
    # Step 1: Get all files
    print("📂 Fetching file list...")
    files = get_all_files()
    print(f"   Found {len(files)} files")
    print()
    
    # Step 2: Process each file
    print("🔄 Processing files...")
    files_data = []
    stats = {"renamed": 0, "modified": 0, "unchanged": 0, "binary_renamed": 0}
    
    for f in files:
        old_path = f['path']
        new_path = get_new_path(old_path, path_renames)
        is_bin = is_binary(old_path)
        
        content = get_file_content(old_path)
        if content is None:
            print(f"   ⚠ Could not fetch: {old_path}")
            continue
        
        modified = False
        
        if is_bin:
            if old_path != new_path:
                stats["binary_renamed"] += 1
                print(f"   📦 Rename (binary): {old_path} → {new_path}")
        else:
            try:
                text_content = content.decode('utf-8')
                new_content = replace_text(text_content, replacements)
                
                if text_content != new_content:
                    modified = True
                    stats["modified"] += 1
                    content = new_content.encode('utf-8')
                
                if old_path != new_path:
                    stats["renamed"] += 1
                    print(f"   📝 Rename: {old_path} → {new_path}")
                elif modified:
                    print(f"   ✏️  Modified: {old_path}")
                else:
                    stats["unchanged"] += 1
                    
            except UnicodeDecodeError:
                is_bin = True
                if old_path != new_path:
                    stats["binary_renamed"] += 1
        
        if old_path != new_path or modified:
            files_data.append({
                'path': old_path,
                'new_path': new_path,
                'content': content if is_bin else content.decode('utf-8'),
                'is_binary': is_bin,
                'modified': modified
            })
    
    print()
    print(f"📊 Summary:")
    print(f"   Renamed:        {stats['renamed']} text files")
    print(f"   Binary renamed: {stats['binary_renamed']} files")
    print(f"   Modified:       {stats['modified']} files")
    print(f"   Unchanged:      {stats['unchanged']} files")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - No changes made")
        print()
        print("To apply changes, run without --dry-run")
        return True
    
    # Step 3: Create and commit
    print("📝 Creating commit actions...")
    actions = create_commit_actions(files_data)
    print(f"   Total actions: {len(actions)}")
    print()
    
    print("🚀 Committing changes...")
    commit_msg = f"refactor: rename {OLD_NAME['upper']} to {NEW_NAME['upper']}"
    if OLD_NAME['upper'] != NEW_NAME['upper']:
        commit_msg += f" ({NEW_NAME['full']})"
    
    success = commit_changes(actions, commit_msg)
    
    print()
    print("=" * 60)
    if success:
        print("✅ Rename complete!")
        print()
        print("⚠️  Don't forget to update snapshots if CLI output changed!")
        print("   The snapshot content must match the new project name.")
    else:
        print("❌ Rename failed - check errors above")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
