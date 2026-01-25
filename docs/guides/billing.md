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

Find it in `billing/output/AR_001_2026_oxy.pdf`

---

## Invoice Numbering

Format: `AR_{sequence}_{year}`

| Example | Meaning |
|---------|---------|
| `AR_001_2026` | 1st invoice of 2026 |
| `AR_015_2026` | 15th invoice of 2026 |

Global sequence across all clients.

---

## Time Tracking Labels

| Label | Meaning |
|-------|---------|
| `billable` | Include in invoice |
| `work::remote` | Remote work (standard rate) |
| `work::onsite` | On-site work (higher rate) |
| `non-billable` | Don't invoice this |

---

## Invoice Templates

Built with [Typst](https://typst.app/) for modern typography (Poppins font).

| Template | Use Case | Currency | VAT |
|----------|----------|----------|-----|
| `invoice-en-us.typ` | US customers | USD | None |
| `invoice-en-eu.typ` | EU customers | EUR | Reverse Charge |
| `rechnung-de.typ` | DE/AT customers | EUR | Reverse Charge |

---

## Directory Structure

```
billing/
├── config/
│   ├── clients.yaml      # Client definitions
│   └── sequences.yaml    # Invoice number tracking
├── templates/
│   ├── invoice-en-us.typ # US (USD)
│   ├── invoice-en-eu.typ # EU (EUR)
│   ├── rechnung-de.typ   # German (EUR)
│   └── logo.jpg
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
    template: "invoice-en-us"
    currency: "USD"
    address:
      line1: "123 Main St"
      city: "New York, NY 10001"
      country: "USA"
    contract_number: "00003154"
    rates:
      remote: 105
      onsite: 120
```

---

## Command Reference

```bash
# Preview without generating
python billing/scripts/generate_invoice.py --client oxy --hours 100 --dry-run

# Generate .typ only (no PDF)
python billing/scripts/generate_invoice.py --client oxy --hours 100 --no-pdf

# Custom invoice date
python billing/scripts/generate_invoice.py --client oxy --hours 100 --date 2025-12-31

# On-site hours
python billing/scripts/generate_invoice.py --client oxy --hours 40 --onsite
```

---

## CI Integration

The `build_invoice` job automatically compiles `.typ` files to PDF when templates change.

Manual trigger: Run pipeline → Select `build_invoice`

---

## Requirements

```bash
# Typst (for PDF generation)
curl -fsSL https://typst.community/typst-install/install.sh | sh

# Python dependencies
pip install pyyaml requests
```

---

## Full Documentation

See [billing/README.md](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/blob/main/billing/README.md) for complete reference.
