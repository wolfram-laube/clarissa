#!/usr/bin/env python3
"""
CLARISSA Timesheet Generator

Generates timesheets from GitLab Time Tracking data.

Usage:
    python generate_timesheet.py --client nemensis --period 2026-01
    python generate_timesheet.py --client oxy --period 2026-01 --lang en
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

import yaml

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
    """Load client configuration."""
    config_file = CONFIG_DIR / "clients.yaml"
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_time_entries(project_id: str, year: int, month: int) -> dict:
    """
    Fetch time tracking entries from GitLab for a specific month.
    
    Returns dict: {day: [(hours, description, issue_iid), ...]}
    """
    if not GITLAB_TOKEN:
        print("❌ GITLAB_TOKEN not set")
        return {}
    
    try:
        import requests
    except ImportError:
        print("❌ 'requests' not installed")
        return {}
    
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Fetch all issues with time tracking
    entries_by_day = defaultdict(list)
    
    # Get issues updated in this period
    url = f"{GITLAB_API_URL}/projects/{project_id}/issues"
    params = {
        "state": "all",
        "per_page": 100,
        "updated_after": (start_date - timedelta(days=30)).isoformat(),
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching issues: {response.status_code}")
        return {}
    
    issues = response.json()
    
    for issue in issues:
        issue_iid = issue["iid"]
        issue_title = issue["title"]
        
        # Get time tracking notes for this issue
        notes_url = f"{GITLAB_API_URL}/projects/{project_id}/issues/{issue_iid}/notes"
        notes_response = requests.get(notes_url, headers=headers, params={"per_page": 100})
        
        if notes_response.status_code != 200:
            continue
        
        notes = notes_response.json()
        
        for note in notes:
            body = note.get("body", "")
            created_at = note.get("created_at", "")
            
            # Parse time tracking notes
            # Format: "added 2h of time spent" or "subtracted 1h of time spent"
            time_match = re.search(r"(added|subtracted)\s+(\d+)h(?:\s+(\d+)m)?\s+of time spent", body)
            
            if time_match:
                action = time_match.group(1)
                hours = int(time_match.group(2))
                minutes = int(time_match.group(3) or 0)
                total_hours = hours + minutes / 60
                
                if action == "subtracted":
                    total_hours = -total_hours
                
                # Parse the date from created_at
                note_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                
                # Check if note is within our month
                if start_date <= note_date.replace(tzinfo=None) < end_date:
                    day = note_date.day
                    
                    # Truncate title if too long
                    short_title = issue_title[:40] + "..." if len(issue_title) > 40 else issue_title
                    
                    entries_by_day[day].append({
                        "hours": total_hours,
                        "description": f"#{issue_iid}: {short_title}",
                        "issue_iid": issue_iid,
                        "note_id": note["id"],
                    })
    
    # Aggregate per day
    daily_entries = {}
    for day, entries in entries_by_day.items():
        total_hours = sum(e["hours"] for e in entries)
        descriptions = "; ".join(e["description"] for e in entries)
        daily_entries[day] = {
            "hours": round(total_hours, 1),
            "description": descriptions,
            "entries": entries,  # Keep original for sync
        }
    
    return daily_entries


def generate_timesheet_typ(
    client_id: str,
    client_config: dict,
    year: int,
    month: int,
    lang: str,
    daily_entries: dict,
    gitlab_data: dict,  # Original data for sync
) -> Path:
    """Generate Typst timesheet file."""
    
    # Load template
    template_file = TEMPLATES_DIR / "timesheet.typ"
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Build daily_entries for Typst
    entries_str = ",\n    ".join(
        f'"{day}": ({data["hours"]}, "{data["description"]}")'
        for day, data in sorted(daily_entries.items())
    )
    
    # Determine country from client config (default AT)
    country = "AT"
    address = client_config.get("address", {})
    if "Deutschland" in address.get("city", "") or "Germany" in address.get("country", ""):
        country = "DE"
    
    # Replace the example call at the end
    new_call = f'''#timesheet(
  year: {year},
  month: {month},
  client_name: "{client_config.get('name', '')}",
  client_short: "{client_config.get('short', '')}",
  project_name: "Consulting Services",
  contract_number: "{client_config.get('contract_number', '')}",
  consultant_name: "Wolfram Laube",
  country: "{country}",
  lang: "{lang}",
  daily_entries: (
    {entries_str}
  ),
)'''
    
    # Replace example timesheet call
    template = re.sub(
        r'// Example:.*?#timesheet\([^)]+\)',
        f'// Generated timesheet\n{new_call}',
        template,
        flags=re.DOTALL
    )
    
    # Create output filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{year}-{month:02d}_timesheet_{client_id}_{lang}.typ"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template)
    
    # Save GitLab sync data (original state for later comparison)
    sync_file = OUTPUT_DIR / f"{year}-{month:02d}_timesheet_{client_id}_{lang}.sync.json"
    sync_data = {
        "client_id": client_id,
        "year": year,
        "month": month,
        "lang": lang,
        "generated_at": datetime.now().isoformat(),
        "gitlab_entries": {str(k): v for k, v in gitlab_data.items()},
    }
    with open(sync_file, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    # Copy logo
    logo_src = TEMPLATES_DIR / "logo.jpg"
    logo_dst = OUTPUT_DIR / "logo.jpg"
    if logo_src.exists() and not logo_dst.exists():
        import shutil
        shutil.copy(logo_src, logo_dst)
    
    print(f"✅ Generated: {output_file}")
    print(f"✅ Sync data: {sync_file}")
    
    return output_file


def compile_pdf(typ_file: Path) -> Path:
    """Compile Typst file to PDF."""
    pdf_file = typ_file.with_suffix(".pdf")
    
    result = subprocess.run(
        ["typst", "compile", str(typ_file), str(pdf_file)],
        capture_output=True,
        text=True,
        cwd=typ_file.parent
    )
    
    if result.returncode != 0:
        print(f"⚠️ Typst warnings/errors:\n{result.stderr}")
    
    if pdf_file.exists():
        print(f"✅ PDF generated: {pdf_file}")
        return pdf_file
    else:
        print("❌ PDF generation failed")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate timesheet from GitLab time tracking")
    parser.add_argument("--client", "-c", required=True, help="Client ID from clients.yaml")
    parser.add_argument("--period", "-p", required=True, help="Period YYYY-MM")
    parser.add_argument("--lang", "-l", default="de", help="Language: en, de, vi, ar, is")
    parser.add_argument("--no-pdf", action="store_true", help="Generate .typ only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched")
    
    args = parser.parse_args()
    
    # Parse period
    try:
        year, month = map(int, args.period.split("-"))
    except ValueError:
        print("❌ Invalid period format. Use YYYY-MM")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    if args.client not in config["clients"]:
        print(f"❌ Unknown client: {args.client}")
        print(f"Available: {', '.join(config['clients'].keys())}")
        sys.exit(1)
    
    client_config = config["clients"][args.client]
    
    print(f"📅 Fetching time entries for {year}-{month:02d}...")
    print(f"👤 Client: {client_config['name']}")
    
    # Fetch from GitLab
    gitlab_data = fetch_time_entries(GITLAB_PROJECT_ID, year, month)
    
    if not gitlab_data:
        print("⚠️ No time entries found in GitLab for this period")
        if not args.dry_run:
            print("   Creating empty timesheet for manual entry...")
            gitlab_data = {}
    
    # Prepare daily entries
    daily_entries = {
        day: {"hours": data["hours"], "description": data["description"]}
        for day, data in gitlab_data.items()
    }
    
    total_hours = sum(d["hours"] for d in daily_entries.values())
    
    print(f"\n📊 Summary:")
    print(f"   Days with entries: {len(daily_entries)}")
    print(f"   Total hours: {total_hours}")
    
    if daily_entries:
        print(f"\n📋 Entries:")
        for day in sorted(daily_entries.keys()):
            data = daily_entries[day]
            print(f"   {day:2d}. → {data['hours']:5.1f}h  {data['description'][:50]}")
    
    if args.dry_run:
        print("\n⚠️ Dry run - no files generated")
        return
    
    # Generate timesheet
    typ_file = generate_timesheet_typ(
        args.client,
        client_config,
        year,
        month,
        args.lang,
        daily_entries,
        gitlab_data,
    )
    
    if not args.no_pdf:
        compile_pdf(typ_file)
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review/edit: {typ_file}")
    print(f"   2. Sync changes: python billing/scripts/sync_timesheet.py {typ_file}")
    print(f"   3. Generate invoice: python billing/scripts/generate_invoice.py --from-timesheet {typ_file}")


if __name__ == "__main__":
    main()
