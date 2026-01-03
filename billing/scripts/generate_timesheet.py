#!/usr/bin/env python3
"""
CLARISSA Timesheet Generator

Generates timesheets from GitLab Time Tracking data.

Usage:
    # Single consultant
    python generate_timesheet.py --client nemensis --period 2026-01 --consultant wolfram
    
    # All consultants for a client
    python generate_timesheet.py --client nemensis --period 2026-01 --all-consultants
    
Requirements:
    - GitLab issues must have label matching client's gitlab_label (e.g., "client:nemensis")
    - Time is tracked via /spend command on issues
    - GITLAB_TOKEN environment variable must be set
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional

try:
    import yaml
    import requests
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   pip install pyyaml requests")
    sys.exit(1)

# Paths
SCRIPT_DIR = Path(__file__).parent
BILLING_DIR = SCRIPT_DIR.parent
CONFIG_DIR = BILLING_DIR / "config"
TEMPLATES_DIR = BILLING_DIR / "templates"
OUTPUT_DIR = BILLING_DIR / "output"

# GitLab API
GITLAB_API_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PROJECT_ID = os.environ.get("GITLAB_PROJECT_ID", "77260390")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")


def load_config() -> dict:
    """Load client and consultant configuration."""
    config_file = CONFIG_DIR / "clients.yaml"
    if not config_file.exists():
        print(f"❌ Config not found: {config_file}")
        sys.exit(1)
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_time_entries(
    project_id: str,
    year: int,
    month: int,
    gitlab_label: str,
    gitlab_username: Optional[str] = None
) -> dict:
    """
    Fetch time tracking entries from GitLab for a specific month.
    
    Args:
        project_id: GitLab project ID
        year: Year (e.g., 2026)
        month: Month (1-12)
        gitlab_label: Label to filter issues (e.g., "client:nemensis")
        gitlab_username: Optional - filter by who spent the time
    
    Returns:
        dict: {day: [(hours, description, issue_title), ...]}
    """
    if not GITLAB_TOKEN:
        print("❌ GITLAB_TOKEN environment variable not set")
        print("   Export your GitLab Personal Access Token:")
        print("   export GITLAB_TOKEN='glpat-xxx'")
        return {}
    
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    entries_by_day = defaultdict(list)
    
    # Fetch issues with the client label
    url = f"{GITLAB_API_URL}/projects/{project_id}/issues"
    params = {
        "labels": gitlab_label,
        "state": "all",
        "per_page": 100,
        "updated_after": (start_date - timedelta(days=7)).isoformat(),
    }
    
    print(f"   Fetching issues with label '{gitlab_label}'...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error fetching issues: {response.status_code}")
        print(f"   {response.text[:200]}")
        return {}
    
    issues = response.json()
    print(f"   Found {len(issues)} issues")
    
    for issue in issues:
        issue_iid = issue["iid"]
        issue_title = issue["title"]
        
        # Get time tracking notes (system notes about /spend)
        notes_url = f"{GITLAB_API_URL}/projects/{project_id}/issues/{issue_iid}/notes"
        notes_params = {"per_page": 100, "sort": "asc"}
        notes_response = requests.get(notes_url, headers=headers, params=notes_params)
        
        if notes_response.status_code != 200:
            continue
        
        notes = notes_response.json()
        
        for note in notes:
            # Only system notes about time tracking
            if not note.get("system", False):
                continue
            
            body = note.get("body", "")
            author = note.get("author", {})
            author_username = author.get("username", "")
            created_at = note.get("created_at", "")
            
            # Filter by username if specified
            if gitlab_username and author_username != gitlab_username:
                continue
            
            # Parse time tracking notes
            # Formats: 
            #   "added 2h of time spent"
            #   "added 2h 30m of time spent"
            #   "added 30m of time spent"
            #   "subtracted 1h of time spent"
            #   "added 4h of time spent at 2026-01-03"
            time_match = re.search(
                r"(added|subtracted)\s+(?:(\d+)h)?\s*(?:(\d+)m)?\s+of time spent(?:\s+at\s+(\d{4}-\d{2}-\d{2}))?",
                body
            )
            
            if time_match:
                action = time_match.group(1)
                hours = int(time_match.group(2) or 0)
                minutes = int(time_match.group(3) or 0)
                specific_date = time_match.group(4)
                
                total_hours = hours + minutes / 60
                
                if action == "subtracted":
                    total_hours = -total_hours
                
                # Use specific date if provided, otherwise note creation date
                if specific_date:
                    entry_date = datetime.strptime(specific_date, "%Y-%m-%d")
                else:
                    entry_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                
                # Check if within our target month
                if start_date <= entry_date.replace(tzinfo=None) < end_date:
                    day = entry_date.day
                    # Truncate description if too long
                    desc = issue_title[:50] + "..." if len(issue_title) > 50 else issue_title
                    entries_by_day[day].append((total_hours, desc))
    
    return dict(entries_by_day)


def generate_timesheet_typ(
    year: int,
    month: int,
    client_id: str,
    client_config: dict,
    consultant_id: str,
    consultant_config: dict,
    entries: dict,
    lang: str = "de"
) -> str:
    """Generate Typst timesheet content."""
    
    # Build daily_entries string
    daily_entries_parts = []
    for day, day_entries in sorted(entries.items()):
        total_hours = sum(h for h, _ in day_entries)
        # Combine descriptions
        descriptions = list(set(d for _, d in day_entries))
        desc = "; ".join(descriptions[:2])  # Max 2 descriptions
        if len(descriptions) > 2:
            desc += f" (+{len(descriptions)-2} more)"
        daily_entries_parts.append(f'    "{day}": ({total_hours}, "{desc}"),')
    
    daily_entries_str = "\n".join(daily_entries_parts) if daily_entries_parts else "    // No entries"
    
    # Determine country from consultant or default
    country = "AT"  # Default
    
    # Get approver info
    approver = client_config.get("approver", {})
    approver_name = approver.get("name", "")
    approver_title = approver.get("title", "")
    
    content = f'''// BLAUWEISS Timesheet - {year}-{month:02d}
// Client: {client_config.get('name', '')}
// Consultant: {consultant_config.get('name', '')}
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

#import "../templates/timesheet.typ": timesheet

#timesheet(
  year: {year},
  month: {month},
  client_name: "{client_config.get('name', '')}",
  client_short: "{client_config.get('short', '')}",
  project_name: "{client_config.get('contract_number', '')}",
  contract_number: "{client_config.get('contract_number', '')}",
  consultant_name: "{consultant_config.get('name', '')}",
  country: "{country}",
  lang: "{lang}",
  approver_name: "{approver_name}",
  approver_title: "{approver_title}",
  daily_entries: (
{daily_entries_str}
  ),
)
'''
    return content


def generate_timesheet(
    client_id: str,
    consultant_id: str,
    year: int,
    month: int,
    lang: str,
    config: dict
) -> Optional[Path]:
    """Generate a single timesheet for one consultant."""
    
    client_config = config["clients"][client_id]
    consultant_config = config["consultants"][consultant_id]
    
    gitlab_label = client_config.get("gitlab_label", f"client:{client_id}")
    gitlab_username = consultant_config.get("gitlab_username")
    
    print(f"\n📋 Generating timesheet:")
    print(f"   Client: {client_config['name']}")
    print(f"   Consultant: {consultant_config['name']} (@{gitlab_username})")
    print(f"   Period: {year}-{month:02d}")
    
    # Fetch time entries
    entries = fetch_time_entries(
        GITLAB_PROJECT_ID,
        year,
        month,
        gitlab_label,
        gitlab_username
    )
    
    if not entries:
        print("   ⚠️ No time entries found")
        return None
    
    # Calculate total
    total_hours = sum(sum(h for h, _ in day_entries) for day_entries in entries.values())
    print(f"   ✅ Found {total_hours:.1f} hours across {len(entries)} days")
    
    # Generate Typst content
    content = generate_timesheet_typ(
        year, month, client_id, client_config,
        consultant_id, consultant_config, entries, lang
    )
    
    # Write output file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{year}-{month:02d}_timesheet_{client_id}_{consultant_id}_{lang}.typ"
    output_file = OUTPUT_DIR / filename
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"   📄 Generated: {output_file.name}")
    
    # Also write sync metadata
    sync_data = {
        "client_id": client_id,
        "consultant_id": consultant_id,
        "year": year,
        "month": month,
        "lang": lang,
        "total_hours": total_hours,
        "entries": {str(k): v for k, v in entries.items()},
        "generated_at": datetime.now().isoformat()
    }
    sync_file = output_file.with_suffix(".sync.json")
    with open(sync_file, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=2)
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate timesheets from GitLab time tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single consultant
    %(prog)s --client nemensis --period 2026-01 --consultant wolfram
    
    # All consultants for a client
    %(prog)s --client nemensis --period 2026-01 --all-consultants
    
Environment:
    GITLAB_TOKEN     GitLab Personal Access Token (required)
    GITLAB_PROJECT_ID  Project ID (default: 77260390)
"""
    )
    parser.add_argument("--client", "-c", required=True, help="Client ID from clients.yaml")
    parser.add_argument("--period", "-p", required=True, help="Period as YYYY-MM")
    parser.add_argument("--consultant", help="Consultant ID (from clients.yaml consultants)")
    parser.add_argument("--all-consultants", action="store_true", help="Generate for all consultants")
    parser.add_argument("--lang", "-l", default="de", help="Language (de, en, vi, ar, is)")
    
    args = parser.parse_args()
    
    # Parse period
    try:
        year, month = map(int, args.period.split("-"))
    except ValueError:
        print(f"❌ Invalid period format: {args.period}")
        print("   Use YYYY-MM (e.g., 2026-01)")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    # Validate client
    if args.client not in config.get("clients", {}):
        print(f"❌ Unknown client: {args.client}")
        available = [k for k in config.get("clients", {}).keys() if not k.startswith("_")]
        print(f"   Available: {', '.join(available)}")
        sys.exit(1)
    
    client_config = config["clients"][args.client]
    
    # Determine which consultants to process
    if args.all_consultants:
        consultant_ids = client_config.get("consultants", [])
        if not consultant_ids:
            print(f"❌ No consultants configured for client '{args.client}'")
            sys.exit(1)
        print(f"🔄 Generating timesheets for {len(consultant_ids)} consultants...")
    elif args.consultant:
        if args.consultant not in config.get("consultants", {}):
            print(f"❌ Unknown consultant: {args.consultant}")
            available = list(config.get("consultants", {}).keys())
            print(f"   Available: {', '.join(available)}")
            sys.exit(1)
        consultant_ids = [args.consultant]
    else:
        print("❌ Specify --consultant or --all-consultants")
        sys.exit(1)
    
    # Generate timesheets
    generated = []
    for consultant_id in consultant_ids:
        result = generate_timesheet(
            args.client,
            consultant_id,
            year,
            month,
            args.lang,
            config
        )
        if result:
            generated.append(result)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Generated {len(generated)} timesheet(s)")
    for f in generated:
        print(f"   📄 {f.name}")
    
    if generated:
        print(f"\nNext steps:")
        print(f"   1. Review and get approvals")
        print(f"   2. Generate invoice:")
        print(f"      python generate_invoice.py --client {args.client} --period {args.period}")


if __name__ == "__main__":
    main()
