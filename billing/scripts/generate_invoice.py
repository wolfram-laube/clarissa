#!/usr/bin/env python3
"""
CLARISSA Invoice Generator

Generates invoices from GitLab Time Tracking data.

Usage:
    python generate_invoice.py --client oxy --period 2025-12
    python generate_invoice.py --client nemensis --period 2025-12 --dry-run
    python generate_invoice.py --client oxy --hours 184 --remote  # Manual entry
"""

import argparse
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


def get_next_invoice_number(client_id: str, client_config: dict, year: int) -> str:
    """Generate next invoice number for client."""
    sequences = load_sequences()
    
    year_str = str(year)
    if year_str not in sequences["sequences"]:
        sequences["sequences"][year_str] = {}
    
    if client_id not in sequences["sequences"][year_str]:
        sequences["sequences"][year_str][client_id] = 1
    
    seq = sequences["sequences"][year_str][client_id]
    prefix = client_config.get("invoice_prefix", "INV")
    short = client_config.get("short", client_id.upper()[:3])
    
    invoice_number = f"{prefix}_{short}{seq:03d}_{year}"
    
    # Increment for next time
    sequences["sequences"][year_str][client_id] = seq + 1
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
            # Check labels for remote/onsite
            issue_labels = [l.lower() for l in issue.get("labels", [])]
            
            if "work::onsite" in issue_labels:
                onsite_seconds += time_spent
            else:
                remote_seconds += time_spent
            
            issue_details.append({
                "iid": issue["iid"],
                "title": issue["title"],
                "time_spent": time_spent / 3600,  # Convert to hours
                "type": "onsite" if "work::onsite" in issue_labels else "remote"
            })
    
    return {
        "remote_hours": round(remote_seconds / 3600, 1),
        "onsite_hours": round(onsite_seconds / 3600, 1),
        "issues": issue_details
    }


def generate_invoice_tex(
    client_id: str,
    client_config: dict,
    remote_hours: float,
    onsite_hours: float,
    invoice_date: datetime,
    invoice_number: str = None
) -> Path:
    """Generate LaTeX invoice file."""
    
    # Get invoice number
    if not invoice_number:
        invoice_number = get_next_invoice_number(
            client_id, client_config, invoice_date.year
        )
    
    # Load template
    template_name = client_config.get("template", "invoice-en-us")
    template_file = TEMPLATES_DIR / f"{template_name}.tex"
    
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Calculate amounts
    rates = client_config.get("rates", {})
    remote_rate = rates.get("remote", 105)
    onsite_rate = rates.get("onsite", 120)
    remote_amount = remote_hours * remote_rate
    onsite_amount = onsite_hours * onsite_rate
    total = remote_amount + onsite_amount
    
    # Format date based on template language
    if "de" in template_name:
        date_str = invoice_date.strftime("%d. %B %Y")
        # German month names
        months_de = {
            "January": "Januar", "February": "Februar", "March": "März",
            "April": "April", "May": "Mai", "June": "Juni",
            "July": "Juli", "August": "August", "September": "September",
            "October": "Oktober", "November": "November", "December": "Dezember"
        }
        for en, de in months_de.items():
            date_str = date_str.replace(en, de)
    else:
        date_str = invoice_date.strftime("%B %d, %Y")
    
    # Address formatting
    address = client_config.get("address", {})
    
    # Replace variables
    replacements = {
        "VAR_INVOICE_NUMBER": invoice_number,
        "VAR_INVOICE_DATE": date_str,
        "VAR_CONTRACT_NUMBER": client_config.get("contract_number", ""),
        "VAR_CLIENT_NAME": client_config.get("name", ""),
        "VAR_CLIENT_ADDRESS": address.get("line1", ""),
        "VAR_CLIENT_CITY": address.get("city", ""),
        "VAR_CLIENT_COUNTRY": address.get("country", ""),
        "VAR_CLIENT_REG_ID": client_config.get("registration_id", ""),
        "VAR_CLIENT_VAT_ID": client_config.get("vat_id", ""),
        "VAR_REMOTE_HOURS": str(int(remote_hours)),
        "VAR_REMOTE_RATE": str(remote_rate),
        "VAR_REMOTE_AMOUNT": str(int(remote_amount)),
        "VAR_ONSITE_HOURS": str(int(onsite_hours)),
        "VAR_ONSITE_RATE": str(onsite_rate),
        "VAR_ONSITE_AMOUNT": str(int(onsite_amount)),
        "VAR_TOTAL_DUE": str(int(total)),
        "VAR_TOTAL_NET": str(int(total)),
    }
    
    for var, value in replacements.items():
        template = template.replace(var, value)
    
    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{invoice_number}.tex"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"✅ Generated: {output_file}")
    return output_file


def compile_pdf(tex_file: Path) -> Path:
    """Compile LaTeX file to PDF."""
    output_dir = tex_file.parent
    
    # Copy logo if not present
    logo_src = TEMPLATES_DIR / "logo.png"
    logo_dst = output_dir / "logo.png"
    if logo_src.exists() and not logo_dst.exists():
        import shutil
        shutil.copy(logo_src, logo_dst)
    
    # Run pdflatex twice (for references)
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"LaTeX error:\n{result.stdout}\n{result.stderr}")
            return None
    
    pdf_file = tex_file.with_suffix(".pdf")
    if pdf_file.exists():
        print(f"✅ PDF generated: {pdf_file}")
        
        # Cleanup aux files
        for ext in [".aux", ".log", ".out"]:
            aux_file = tex_file.with_suffix(ext)
            if aux_file.exists():
                aux_file.unlink()
        
        return pdf_file
    else:
        print("❌ PDF generation failed")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate invoice from GitLab time tracking")
    parser.add_argument("--client", "-c", required=True, help="Client ID from clients.yaml")
    parser.add_argument("--period", "-p", help="Billing period (YYYY-MM)")
    parser.add_argument("--hours", "-h", type=float, help="Manual hours entry")
    parser.add_argument("--remote", action="store_true", help="Hours are remote (default)")
    parser.add_argument("--onsite", action="store_true", help="Hours are on-site")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--no-pdf", action="store_true", help="Generate .tex only, no PDF")
    parser.add_argument("--date", help="Invoice date (YYYY-MM-DD), default: today")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    if args.client not in config["clients"]:
        print(f"❌ Unknown client: {args.client}")
        print(f"Available clients: {', '.join(config['clients'].keys())}")
        sys.exit(1)
    
    client_config = config["clients"][args.client]
    
    # Determine hours
    remote_hours = 0
    onsite_hours = 0
    
    if args.hours:
        # Manual entry
        if args.onsite:
            onsite_hours = args.hours
        else:
            remote_hours = args.hours
    elif args.period:
        # Fetch from GitLab
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
        print("❌ Specify either --period or --hours")
        sys.exit(1)
    
    # Invoice date
    if args.date:
        invoice_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        invoice_date = datetime.now()
    
    # Calculate totals
    rates = client_config.get("rates", {})
    remote_rate = rates.get("remote", 105)
    onsite_rate = rates.get("onsite", 120)
    total = (remote_hours * remote_rate) + (onsite_hours * onsite_rate)
    currency = client_config.get("currency", "USD")
    
    print(f"\n📄 Invoice Preview:")
    print(f"   Client: {client_config['name']}")
    print(f"   Template: {client_config['template']}")
    print(f"   Remote: {remote_hours}h × {currency} {remote_rate} = {currency} {remote_hours * remote_rate}")
    print(f"   On-site: {onsite_hours}h × {currency} {onsite_rate} = {currency} {onsite_hours * onsite_rate}")
    print(f"   Total: {currency} {total}")
    
    if args.dry_run:
        print("\n⚠️  Dry run - no files generated")
        return
    
    # Generate
    tex_file = generate_invoice_tex(
        args.client,
        client_config,
        remote_hours,
        onsite_hours,
        invoice_date
    )
    
    if not args.no_pdf:
        compile_pdf(tex_file)


if __name__ == "__main__":
    main()
