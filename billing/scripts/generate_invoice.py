#!/usr/bin/env python3
"""
CLARISSA Invoice Generator (Typst)

Generates professional invoices from GitLab Time Tracking data or timesheets.

Usage:
    # From timesheet (recommended)
    python generate_invoice.py --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ
    
    # Direct from GitLab (legacy)
    python generate_invoice.py --client oxy --period 2025-12
    
    # Manual entry
    python generate_invoice.py --client nemensis --hours 184 --remote
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
BILLING_DIR = SCRIPT_DIR.parent
CONFIG_DIR = BILLING_DIR / "config"
TEMPLATES_DIR = BILLING_DIR / "templates"
OUTPUT_DIR = BILLING_DIR / "output"

# GitLab API (optional - for time tracking integration)
GITLAB_API_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PROJECT_ID = os.environ.get("GITLAB_PROJECT_ID", "77260390")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")


def load_config() -> dict:
    """Load client configuration."""
    config_file = CONFIG_DIR / "clients.yaml"
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_sequences() -> dict:
    """Load invoice sequence numbers."""
    seq_file = CONFIG_DIR / "sequences.yaml"
    with open(seq_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_sequences(sequences: dict) -> None:
    """Save updated invoice sequence numbers."""
    seq_file = CONFIG_DIR / "sequences.yaml"
    with open(seq_file, "w", encoding="utf-8") as f:
        yaml.dump(sequences, f, default_flow_style=False)


def get_next_invoice_number(year: int, dry_run: bool = False) -> str:
    """Generate next invoice number (global AR_XXX_YYYY format)."""
    sequences = load_sequences()
    
    year_str = str(year)
    if year_str not in sequences["sequences"]:
        sequences["sequences"][year_str] = 1
    
    seq = sequences["sequences"][year_str]
    invoice_number = f"AR_{seq:03d}_{year}"
    
    # Increment for next time (unless dry run)
    if not dry_run:
        sequences["sequences"][year_str] = seq + 1
        save_sequences(sequences)
    
    return invoice_number


def fetch_gitlab_time(project_id: str, period: str, labels: list = None) -> dict:
    """
    Fetch time tracking data from GitLab API.
    
    Returns dict with:
        remote_hours: float
        onsite_hours: float
        issues: list of issue details
    """
    if not GITLAB_TOKEN:
        print("Warning: GITLAB_TOKEN not set. Cannot fetch time data from GitLab.")
        return None
    
    try:
        import requests
    except ImportError:
        print("Warning: 'requests' not installed. Cannot fetch from GitLab.")
        return None
    
    # Parse period (YYYY-MM)
    year, month = map(int, period.split("-"))
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    # Fetch issues with time spent
    url = f"{GITLAB_API_URL}/projects/{project_id}/issues"
    params = {
        "state": "all",
        "updated_after": start_date.isoformat(),
        "updated_before": end_date.isoformat(),
        "per_page": 100
    }
    
    if labels:
        params["labels"] = ",".join(labels)
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching issues: {response.status_code}")
        return None
    
    issues = response.json()
    
    remote_seconds = 0
    onsite_seconds = 0
    issue_details = []
    
    for issue in issues:
        time_spent = issue.get("time_stats", {}).get("total_time_spent", 0)
        if time_spent > 0:
            issue_labels = [l.lower() for l in issue.get("labels", [])]
            
            if "work::onsite" in issue_labels:
                onsite_seconds += time_spent
            else:
                remote_seconds += time_spent
            
            issue_details.append({
                "iid": issue["iid"],
                "title": issue["title"],
                "time_spent": time_spent / 3600,
                "type": "onsite" if "work::onsite" in issue_labels else "remote"
            })
    
    return {
        "remote_hours": round(remote_seconds / 3600, 1),
        "onsite_hours": round(onsite_seconds / 3600, 1),
        "issues": issue_details
    }


def format_date(date: datetime, lang: str) -> str:
    """Format date based on language."""
    if lang == "de":
        months_de = {
            1: "Januar", 2: "Februar", 3: "März", 4: "April",
            5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
        }
        return f"{date.day:02d}. {months_de[date.month]} {date.year}"
    else:
        return date.strftime("%B %d, %Y")


def generate_invoice_typst(
    client_id: str,
    client_config: dict,
    remote_hours: float,
    onsite_hours: float,
    invoice_date: datetime,
    invoice_number: str,
) -> Path:
    """Generate Typst invoice file."""
    
    # Determine template and language
    template_name = client_config.get("template", "invoice-en-us")
    if "de" in template_name:
        lang = "de"
    else:
        lang = "en"
    
    # Load template
    template_file = TEMPLATES_DIR / f"{template_name}.typ"
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Calculate amounts
    rates = client_config.get("rates", {})
    remote_rate = rates.get("remote", 105)
    onsite_rate = rates.get("onsite", 120)
    
    # Format date
    date_str = format_date(invoice_date, lang)
    
    # Build address
    address = client_config.get("address", {})
    
    # Create customized invoice by replacing the example data section
    # Find and replace the invoice() call at the end
    invoice_call = f'''#invoice(
  invoice_number: "{invoice_number}",
  invoice_date: "{date_str}",
  client_name: "{client_config.get('name', '')}",
  client_address: "{address.get('line1', '')}",
  client_city: "{address.get('city', '')}",'''
    
    if "eu" in template_name or "de" in template_name:
        invoice_call += f'''
  client_reg_id: "{client_config.get('registration_id', '')}",
  client_vat_id: "{client_config.get('vat_id', '')}",'''
    else:
        invoice_call += f'''
  client_country: "{address.get('country', '')}",'''
    
    invoice_call += f'''
  contract_number: "{client_config.get('contract_number', '')}",
  remote_hours: {int(remote_hours)},
  remote_rate: {remote_rate},
  onsite_hours: {int(onsite_hours)},
  onsite_rate: {onsite_rate},
)'''
    
    # Replace the example invoice call
    template = re.sub(
        r'#invoice\([^)]+\)',
        invoice_call,
        template,
        flags=re.DOTALL
    )
    
    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{invoice_number}_{client_id}.typ"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template)
    
    # Copy logo if needed
    logo_src = TEMPLATES_DIR / "logo.jpg"
    logo_dst = OUTPUT_DIR / "logo.jpg"
    if logo_src.exists() and not logo_dst.exists():
        import shutil
        shutil.copy(logo_src, logo_dst)
    
    print(f"✅ Generated: {output_file}")
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
        print(f"Typst error:\n{result.stderr}")
        return None
    
    if pdf_file.exists():
        print(f"✅ PDF generated: {pdf_file}")
        return pdf_file
    else:
        print("❌ PDF generation failed")
        return None


def parse_timesheet_for_invoice(typ_file: Path) -> dict:
    """
    Parse a timesheet .typ file and extract hours for invoice.
    
    Returns: {
        "client_id": str,
        "year": int,
        "month": int,
        "total_hours": float,
        "daily_entries": dict,
    }
    """
    # Load sync data for metadata
    sync_file = typ_file.with_suffix(".sync.json")
    if sync_file.exists():
        with open(sync_file, "r", encoding="utf-8") as f:
            sync_data = json.load(f)
    else:
        sync_data = {}
    
    # Parse timesheet
    with open(typ_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract daily entries
    match = re.search(r'daily_entries:\s*\((.*?)\)\s*,?\s*\)', content, re.DOTALL)
    if not match:
        return None
    
    entries_block = match.group(1)
    
    total_hours = 0
    daily_entries = {}
    
    for entry_match in re.finditer(r'"(\d+)":\s*\((\d+(?:\.\d+)?),\s*"([^"]*)"\)', entries_block):
        day = int(entry_match.group(1))
        hours = float(entry_match.group(2))
        description = entry_match.group(3)
        daily_entries[day] = {"hours": hours, "description": description}
        total_hours += hours
    
    # Extract year/month from filename or content
    year = sync_data.get("year")
    month = sync_data.get("month")
    client_id = sync_data.get("client_id")
    
    if not year or not month:
        # Try to parse from filename: 2026-01_timesheet_nemensis_de.typ
        name_match = re.match(r'(\d{4})-(\d{2})_timesheet_(\w+)', typ_file.stem)
        if name_match:
            year = int(name_match.group(1))
            month = int(name_match.group(2))
            client_id = name_match.group(3)
    
    return {
        "client_id": client_id,
        "year": year,
        "month": month,
        "total_hours": total_hours,
        "daily_entries": daily_entries,
        "timesheet_file": typ_file,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate invoice from timesheet or GitLab (Typst)")
    parser.add_argument("--from-timesheet", "-t", help="Generate from timesheet .typ file")
    parser.add_argument("--client", "-c", help="Client ID from clients.yaml")
    parser.add_argument("--period", "-p", help="Billing period (YYYY-MM)")
    parser.add_argument("--hours", type=float, help="Manual hours entry")
    parser.add_argument("--remote", action="store_true", help="Hours are remote (default)")
    parser.add_argument("--onsite", action="store_true", help="Hours are on-site")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--no-pdf", action="store_true", help="Generate .typ only, no PDF")
    parser.add_argument("--date", help="Invoice date (YYYY-MM-DD), default: today")
    parser.add_argument("--upload", action="store_true", help="Upload to Google Drive after generation")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Mode 1: From timesheet
    if args.from_timesheet:
        typ_file = Path(args.from_timesheet)
        if not typ_file.exists():
            typ_file = OUTPUT_DIR / args.from_timesheet
        
        if not typ_file.exists():
            print(f"❌ Timesheet not found: {args.from_timesheet}")
            sys.exit(1)
        
        print(f"📄 Reading timesheet: {typ_file}")
        
        timesheet_data = parse_timesheet_for_invoice(typ_file)
        if not timesheet_data:
            print("❌ Could not parse timesheet")
            sys.exit(1)
        
        client_id = timesheet_data["client_id"]
        if client_id not in config["clients"]:
            print(f"❌ Unknown client in timesheet: {client_id}")
            sys.exit(1)
        
        client_config = config["clients"][client_id]
        remote_hours = timesheet_data["total_hours"]
        onsite_hours = 0  # TODO: Support onsite in timesheet
        
        # Invoice date from timesheet period
        if args.date:
            invoice_date = datetime.strptime(args.date, "%Y-%m-%d")
        else:
            # Default to end of timesheet month
            year = timesheet_data["year"]
            month = timesheet_data["month"]
            if month == 12:
                invoice_date = datetime(year + 1, 1, 1)
            else:
                invoice_date = datetime(year, month + 1, 1)
        
        print(f"📊 From timesheet:")
        print(f"   Period: {timesheet_data['year']}-{timesheet_data['month']:02d}")
        print(f"   Days with entries: {len(timesheet_data['daily_entries'])}")
        print(f"   Total hours: {remote_hours}")
    
    # Mode 2: Direct (legacy)
    else:
        if not args.client:
            print("❌ Specify --client or --from-timesheet")
            sys.exit(1)
        
        if args.client not in config["clients"]:
            print(f"❌ Unknown client: {args.client}")
            print(f"Available clients: {', '.join(config['clients'].keys())}")
            sys.exit(1)
        
        client_id = args.client
        client_config = config["clients"][client_id]
        
        # Determine hours
        remote_hours = 0
        onsite_hours = 0
        
        if args.hours:
            if args.onsite:
                onsite_hours = args.hours
            else:
                remote_hours = args.hours
        elif args.period:
            time_data = fetch_gitlab_time(GITLAB_PROJECT_ID, args.period)
            if time_data:
                remote_hours = time_data["remote_hours"]
                onsite_hours = time_data["onsite_hours"]
                print(f"📊 Time from GitLab:")
                print(f"   Remote: {remote_hours}h")
                print(f"   On-site: {onsite_hours}h")
                print(f"   Issues: {len(time_data['issues'])}")
            else:
                print("❌ Could not fetch time data from GitLab")
                sys.exit(1)
        else:
            print("❌ Specify --period, --hours, or --from-timesheet")
            sys.exit(1)
        
        # Invoice date
        if args.date:
            invoice_date = datetime.strptime(args.date, "%Y-%m-%d")
        else:
            invoice_date = datetime.now()
    
    # Get invoice number
    invoice_number = get_next_invoice_number(invoice_date.year, dry_run=args.dry_run)
    
    # Calculate totals
    rates = client_config.get("rates", {})
    remote_rate = rates.get("remote", 105)
    onsite_rate = rates.get("onsite", 120)
    total = (remote_hours * remote_rate) + (onsite_hours * onsite_rate)
    currency = client_config.get("currency", "USD")
    
    print(f"\n📄 Invoice Preview:")
    print(f"   Number: {invoice_number}")
    print(f"   Client: {client_config['name']}")
    print(f"   Template: {client_config['template']}")
    print(f"   Remote: {remote_hours}h × {currency} {remote_rate} = {currency} {remote_hours * remote_rate}")
    print(f"   On-site: {onsite_hours}h × {currency} {onsite_rate} = {currency} {onsite_hours * onsite_rate}")
    print(f"   Total: {currency} {total}")
    
    if args.dry_run:
        print("\n⚠️  Dry run - no files generated")
        return
    
    # Generate invoice
    typ_file = generate_invoice_typst(
        client_id,
        client_config,
        remote_hours,
        onsite_hours,
        invoice_date,
        invoice_number
    )
    
    # Also compile timesheet PDF if from-timesheet mode
    if args.from_timesheet:
        timesheet_typ = Path(args.from_timesheet)
        if not timesheet_typ.exists():
            timesheet_typ = OUTPUT_DIR / args.from_timesheet
        timesheet_pdf = compile_pdf(timesheet_typ)
        if timesheet_pdf:
            print(f"📎 Timesheet attached: {timesheet_pdf}")
    
    if not args.no_pdf:
        invoice_pdf = compile_pdf(typ_file)
    
    # Upload to Google Drive
    if args.upload and not args.dry_run:
        try:
            from upload_to_drive import upload_file, get_credentials, ensure_folder_path
            from googleapiclient.discovery import build
            
            print("\n📤 Uploading to Google Drive...")
            
            credentials = get_credentials()
            service = build('drive', 'v3', credentials=credentials)
            
            root_folder = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
            if root_folder:
                # Create folder structure: YYYY/MM_client/
                if args.from_timesheet:
                    year = timesheet_data["year"]
                    month = timesheet_data["month"]
                else:
                    year = invoice_date.year
                    month = invoice_date.month
                
                folder_path = f"{year}/{month:02d}_{client_id}"
                target_folder = ensure_folder_path(service, root_folder, folder_path)
                
                # Upload invoice PDF
                if invoice_pdf and invoice_pdf.exists():
                    upload_file(service, target_folder, invoice_pdf)
                
                # Upload timesheet PDF if exists
                if args.from_timesheet:
                    timesheet_pdf = Path(args.from_timesheet).with_suffix(".pdf")
                    if timesheet_pdf.exists():
                        upload_file(service, target_folder, timesheet_pdf)
                
                print(f"🔗 https://drive.google.com/drive/folders/{target_folder}")
            else:
                print("⚠️ GOOGLE_DRIVE_FOLDER_ID not set - skipping upload")
        except ImportError:
            print("⚠️ Google API libraries not installed - skipping upload")
        except Exception as e:
            print(f"⚠️ Upload failed: {e}")
    
    print(f"\n✅ Invoice package complete!")


if __name__ == "__main__":
    main()
