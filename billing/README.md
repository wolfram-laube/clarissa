# 💰 CLARISSA Billing System (Typst)

Generate professional invoices from GitLab Time Tracking data using [Typst](https://typst.app/).

## Quick Start

```bash
# Generate invoice from manual hours
python billing/scripts/generate_invoice.py --client oxy --hours 184

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
│   └── sequences.yaml    # Invoice number tracking (AR_XXX_YYYY)
├── templates/
│   ├── invoice-en-us.typ # US customers (USD, no VAT)
│   ├── invoice-en-eu.typ # EU customers (EUR, reverse charge)
│   ├── rechnung-de.typ   # DE/AT customers (German, reverse charge)
│   └── logo.jpg          # Company logo
├── output/               # Generated invoices (.typ + .pdf)
├── scripts/
│   └── generate_invoice.py
└── README.md
```

## Invoice Templates

| Template | Use Case | Currency | VAT | Language |
|----------|----------|----------|-----|----------|
| `invoice-en-us` | US customers | USD | None | English |
| `invoice-en-eu` | EU customers | EUR | Reverse Charge | English |
| `rechnung-de` | DE/AT customers | EUR | Reverse Charge | German |

All templates use **Poppins** font for a modern, clean look.

## Invoice Numbering

Format: `AR_{sequence}_{year}`

Examples:
- `AR_001_2026` - First invoice of 2026
- `AR_015_2026` - 15th invoice of 2026

Global sequence across all clients, tracked in `config/sequences.yaml`.

## Workflow

### 1. Track Time in GitLab

```
/spend 2h              # Log 2 hours
/spend 4h 2025-12-15   # Log on specific date
```

Labels:
- `work::remote` - Remote work (default rate)
- `work::onsite` - On-site work (higher rate)

### 2. Generate Invoice

```bash
python billing/scripts/generate_invoice.py \
    --client nemensis \
    --period 2025-12
```

### 3. Get Your PDF

Output in `billing/output/AR_001_2026_nemensis.pdf`

## Adding a New Client

Edit `billing/config/clients.yaml`:

```yaml
clients:
  newclient:
    name: "New Client Inc."
    short: "NC"
    template: "invoice-en-us"  # or invoice-en-eu, rechnung-de
    currency: "USD"            # or EUR
    address:
      line1: "123 Main St"
      city: "New York, NY 10001"
      country: "USA"
    contract_number: "00003154"
    # For EU clients, add:
    # registration_id: "KVK: 12345678"
    # vat_id: "NL123456789B01"
    rates:
      remote: 105
      onsite: 120
```

## Command Reference

```bash
# Basic usage
python billing/scripts/generate_invoice.py --client CLIENT --hours HOURS

# Options
  --client, -c    Client ID (required)
  --period, -p    Billing period YYYY-MM (fetches from GitLab)
  --hours         Manual hours entry
  --remote        Hours are remote (default)
  --onsite        Hours are on-site
  --dry-run       Preview without generating
  --no-pdf        Generate .typ only
  --date          Invoice date YYYY-MM-DD (default: today)
```

## Requirements

### Typst

```bash
# Linux
curl -fsSL https://typst.community/typst-install/install.sh | sh

# macOS
brew install typst

# Or download from https://github.com/typst/typst/releases
```

### Python

```bash
pip install pyyaml requests
```

### Fonts

Templates use **Poppins** font. Install if not available:

```bash
# Ubuntu/Debian
sudo apt install fonts-poppins

# Or download from Google Fonts
```

## CI Integration

The CI pipeline automatically builds invoices when `.typ` files are changed:

```yaml
build_invoice:
  stage: build
  image: ghcr.io/typst/typst:latest
  script:
    - typst compile billing/output/*.typ
  artifacts:
    paths:
      - billing/output/*.pdf
```

## Why Typst?

- ✅ Modern, clean typography
- ✅ Fast compilation (10x faster than LaTeX)
- ✅ Simple, readable syntax
- ✅ No complex package management
- ✅ Built-in PDF generation
