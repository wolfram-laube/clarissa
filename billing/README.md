# 💰 CLARISSA Billing System

Generate professional invoices from GitLab Time Tracking data.

## Quick Start

```bash
# Generate invoice from manual hours
python billing/scripts/generate_invoice.py --client oxy --hours 184 --remote

# Generate invoice from GitLab time tracking
export GITLAB_TOKEN="your-token"
python billing/scripts/generate_invoice.py --client nemensis --period 2025-12

# Preview without generating (dry run)
python billing/scripts/generate_invoice.py --client oxy --hours 184 --dry-run
```

## Directory Structure

```
billing/
├── config/
│   ├── clients.yaml      # Client definitions, rates, templates
│   └── sequences.yaml    # Invoice number tracking
├── templates/
│   ├── invoice-en-us.tex # US customers (USD, no VAT)
│   ├── invoice-en-eu.tex # EU customers (EUR, reverse charge)
│   ├── rechnung-de.tex   # DE/AT customers (German, reverse charge)
│   └── logo.png          # Company logo
├── output/               # Generated invoices
│   ├── OP_OXY001_2025.tex
│   └── OP_OXY001_2025.pdf
├── scripts/
│   └── generate_invoice.py
└── README.md
```

## Workflow

### 1. Track Time in GitLab

Use GitLab quick actions in issues:

```
/spend 2h              # Log 2 hours
/spend 4h 2025-12-15   # Log 4 hours on specific date
/estimate 8h           # Set estimate
```

Label issues for billing:
- `billable` - Include in invoice
- `work::remote` - Remote work (default rate)
- `work::onsite` - On-site work (higher rate)
- `non-billable` - Exclude from invoice

### 2. Generate Invoice

```bash
# From GitLab time tracking
python billing/scripts/generate_invoice.py \
    --client oxy \
    --period 2025-12

# Manual entry
python billing/scripts/generate_invoice.py \
    --client oxy \
    --hours 184 \
    --remote
```

### 3. Review and Send

Generated files in `billing/output/`:
- `.tex` - LaTeX source (editable)
- `.pdf` - Final invoice

## Client Configuration

Edit `billing/config/clients.yaml`:

```yaml
clients:
  oxy:
    name: "Occidental Petroleum Corporation"
    short: "OXY"
    template: "invoice-en-us"    # Which template to use
    currency: "USD"
    address:
      line1: "5 Greenway Plaza"
      city: "Houston, TX 77046"
      country: "USA"
    contract_number: "00003151"
    rates:
      remote: 105               # USD/EUR per hour
      onsite: 120
    invoice_prefix: "OP"        # For invoice number
```

## Templates

| Template | Use Case | Currency | VAT |
|----------|----------|----------|-----|
| `invoice-en-us` | US customers | USD | None |
| `invoice-en-eu` | EU customers (English) | EUR | Reverse Charge |
| `rechnung-de` | DE/AT customers | EUR | Reverse Charge |

### Customizing Templates

Templates use LaTeX with variables:
- `VAR_INVOICE_NUMBER` - Auto-generated
- `VAR_CLIENT_NAME` - From config
- `VAR_REMOTE_HOURS` - Hours tracked
- etc.

To modify layout, edit the `.tex` files directly.

## Invoice Numbering

Format: `{PREFIX}_{SHORT}{SEQ}_{YEAR}`

Example: `OP_OXY001_2025`

Sequences tracked in `config/sequences.yaml` - auto-incremented.

## Requirements

```bash
# LaTeX (for PDF generation)
sudo apt install texlive-latex-recommended texlive-latex-extra texlive-lang-german

# Python
pip install pyyaml requests
```

## Environment Variables

```bash
export GITLAB_TOKEN="glpat-xxx"           # For time tracking integration
export GITLAB_PROJECT_ID="77260390"       # Project to fetch from
export GITLAB_API_URL="https://gitlab.com/api/v4"
```

## Command Reference

```
usage: generate_invoice.py [-h] --client CLIENT [--period PERIOD]
                           [--hours HOURS] [--remote] [--onsite]
                           [--dry-run] [--no-pdf] [--date DATE]

Options:
  --client, -c    Client ID from clients.yaml (required)
  --period, -p    Billing period YYYY-MM (fetches from GitLab)
  --hours         Manual hours entry
  --remote        Hours are remote work (default)
  --onsite        Hours are on-site work
  --dry-run       Preview without generating files
  --no-pdf        Generate .tex only, skip PDF compilation
  --date          Invoice date YYYY-MM-DD (default: today)
```

## Tips

### Multiple Line Items

For complex invoices, edit the generated `.tex` file before compiling:
1. Generate with `--no-pdf`
2. Edit the `.tex` file
3. Run `pdflatex` manually

### Batch Processing

```bash
# Generate invoices for all clients for a period
for client in oxy nemensis example_nl; do
    python billing/scripts/generate_invoice.py -c $client -p 2025-12
done
```

### Logo

Place your logo as `billing/templates/logo.png` (recommended: 400x150px).
