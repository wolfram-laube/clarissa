# 💰 Billing & Time Tracking

How to track time and generate invoices for CLARISSA projects.

---

## Quick Start

### 1. Track Time in GitLab

In any issue comment, use:

```
/spend 2h              # Log 2 hours today
/spend 4h 2025-12-15   # Log 4 hours on specific date
/estimate 8h           # Set time estimate
```

### 2. Generate Invoice

```bash
# From GitLab time tracking
python billing/scripts/generate_invoice.py --client oxy --period 2025-12

# Manual hours entry
python billing/scripts/generate_invoice.py --client oxy --hours 184
```

### 3. Get Your PDF

Find it in `billing/output/OP_OXY001_2025.pdf`

---

## Time Tracking Labels

Use these labels on issues for proper billing categorization:

| Label | Meaning |
|-------|---------|
| `billable` | Include in invoice |
| `work::remote` | Remote work (standard rate) |
| `work::onsite` | On-site work (higher rate) |
| `non-billable` | Don't invoice this |

---

## Invoice Templates

| Template | Use Case | Currency | VAT |
|----------|----------|----------|-----|
| `invoice-en-us` | US customers | USD | None |
| `invoice-en-eu` | EU customers (English) | EUR | Reverse Charge |
| `rechnung-de` | DE/AT customers (German) | EUR | Reverse Charge |

---

## Directory Structure

```
billing/
├── config/
│   ├── clients.yaml      # Client definitions
│   └── sequences.yaml    # Invoice number tracking
├── templates/
│   ├── invoice-en-us.tex
│   ├── invoice-en-eu.tex
│   └── rechnung-de.tex
├── scripts/
│   └── generate_invoice.py
└── output/               # Generated invoices
```

---

## Adding a New Client

Edit `billing/config/clients.yaml`:

```yaml
clients:
  newclient:
    name: "New Client Inc."
    short: "NC"
    template: "invoice-en-us"  # or invoice-en-eu, rechnung-de
    currency: "USD"
    address:
      line1: "123 Main St"
      city: "New York, NY 10001"
      country: "USA"
    contract_number: "00003154"
    rates:
      remote: 105
      onsite: 120
    invoice_prefix: "NC"
```

---

## Command Reference

```bash
# Preview without generating
python billing/scripts/generate_invoice.py --client oxy --hours 100 --dry-run

# Generate .tex only (no PDF)
python billing/scripts/generate_invoice.py --client oxy --hours 100 --no-pdf

# Custom invoice date
python billing/scripts/generate_invoice.py --client oxy --hours 100 --date 2025-12-31

# On-site hours
python billing/scripts/generate_invoice.py --client oxy --hours 40 --onsite
```

---

## Requirements

```bash
# LaTeX (for PDF generation)
sudo apt install texlive-latex-recommended texlive-latex-extra texlive-lang-german

# Python dependencies
pip install pyyaml requests
```

---

## Full Documentation

See [billing/README.md](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/blob/main/billing/README.md) for complete reference.
