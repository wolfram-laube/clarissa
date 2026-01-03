# 💰 Rechnungs-Workflow - Schritt für Schritt

> **TL;DR:** Zeit in GitLab tracken → Timesheet generieren → Prüfen/Freigeben → Rechnung erstellen → Automatisch in Google Drive

---

## 🎯 Übersicht

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  /spend 4h  │ →  │  Timesheet  │ →  │  Rechnung   │ →  │Google Drive │
│  (GitLab)   │    │    .typ     │    │    .typ     │    │    📁       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       │                  ↓                  │
       │           ┌─────────────┐           │
       │           │  Freigabe   │           │
       │           │ (Approver)  │           │
       │           └─────────────┘           │
       │                                     │
       └──────────── clients.yaml ───────────┘
                   (Stundensätze, 
                    Adressen, etc.)
```

---

## 📁 Client-Konfiguration

Alle Client-Daten werden zentral in `billing/config/clients.yaml` verwaltet:

```yaml
clients:
  nemensis:
    name: "nemensis AG Deutschland"
    short: "NEM"
    address:
      street: "Alter Wall 69"
      city: "D - 20457 Hamburg"
    reg_id: "HRB. NR.: 181535 Hamburg"
    vat_id: "DE310161615"
    contract_number: "00003153"
    template: "rechnung-de"      # Welches Rechnungstemplate
    currency: "EUR"
    rates:
      remote: 105                # EUR/Stunde remote
      onsite: 120                # EUR/Stunde vor Ort
    approver:
      name: "Max Mustermann"     # Wer gibt Timesheets frei
      title: "Projektleiter"
```

**Neuen Client hinzufügen:**
```bash
vim billing/config/clients.yaml
# → Neuen Eintrag nach dem _template Muster anlegen
```

---

## 📋 Schritt 1: Zeit tracken (täglich)

In **jedem GitLab Issue** das du bearbeitest:

```
/spend 4h                    # 4 Stunden heute
/spend 2h 2026-01-15         # 2 Stunden am 15. Januar
/spend 30m                   # 30 Minuten
```

---

## 📋 Schritt 2: Timesheet generieren (Ende des Monats)

```bash
python billing/scripts/generate_timesheet.py \
    --client nemensis \
    --period 2026-01 \
    --lang de
```

Das Script:
1. Liest `/spend` Einträge aus GitLab
2. Holt Client-Daten aus `clients.yaml` (inkl. Approver)
3. Generiert `billing/output/2026-01_timesheet_nemensis_de.typ`

**Output Timesheet enthält:**
- Consultant Name (aus Script-Aufruf oder Config)
- Client Name (aus `clients.yaml`)
- Approver Name + Title (aus `clients.yaml`)
- Unterschriftsfelder für beide Parteien

---

## 📋 Schritt 3: Timesheet Freigabe

1. **PDF prüfen** - Stimmen alle Einträge?
2. **Unterschrift einholen** - Approver unterzeichnet
3. **Scan/Digital archivieren** (optional)

---

## 📋 Schritt 4: Rechnung generieren

```bash
python billing/scripts/generate_invoice.py \
    --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ
```

Das Script:
1. Liest Timesheet → extrahiert Stunden
2. Holt Stundensätze aus `clients.yaml`
3. Berechnet: `184h × EUR 105 = EUR 19.320`
4. Generiert Rechnung mit korrektem Template (DE/US/EU)

**Woher kommen die Daten?**

| Daten | Quelle |
|-------|--------|
| Stunden | Timesheet (aus GitLab /spend) |
| Stundensatz | `clients.yaml` → rates.remote/onsite |
| Kundenadresse | `clients.yaml` → address |
| USt-ID | `clients.yaml` → vat_id |
| Template (DE/US) | `clients.yaml` → template |

---

## 📋 Schritt 5: Commit & Automatischer Upload

```bash
git add billing/output/
git commit -m "billing: Januar 2026 nemensis"
git push
```

**CI Pipeline macht automatisch:**
1. ✅ `build_invoice` - Kompiliert `.typ` → `.pdf`
2. ✅ `upload_invoice` - Lädt zu Google Drive hoch

---

## 📁 Google Drive Struktur

```
BLAUWEISS-EDV-LLC/
└── 2026/
    ├── 01_nemensis/
    │   └── 2026-01_timesheet_nemensis_de.pdf
    └── nemensis/
        └── AR_001_2026_nemensis.pdf
```

🔗 https://drive.google.com/drive/folders/1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs

---

## ⚡ Quick Reference

```bash
# === MONATLICHER WORKFLOW ===

# 1. Timesheet generieren (liest GitLab + clients.yaml)
python billing/scripts/generate_timesheet.py -c nemensis -p 2026-01 --lang de

# 2. Prüfen & Freigabe einholen
open billing/output/2026-01_timesheet_nemensis_de.pdf

# 3. Rechnung generieren (liest Stundensätze aus clients.yaml)
python billing/scripts/generate_invoice.py --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ

# 4. Commit → CI macht den Rest
git add billing/output/ && git commit -m "billing: Januar 2026 nemensis" && git push
```

---

## 🔧 Verfügbare Templates

| Template | Sprache | Währung | MwSt | Client-Config |
|----------|---------|---------|------|---------------|
| `rechnung-de.typ` | Deutsch | EUR | Reverse Charge | `template: "rechnung-de"` |
| `invoice-en-us.typ` | Englisch | USD | Keine | `template: "invoice-en-us"` |
| `invoice-en-eu.typ` | Englisch | EUR | Reverse Charge | `template: "invoice-en-eu"` |

---

## 🆘 Troubleshooting

### "Unknown client: xyz"
→ Client in `billing/config/clients.yaml` hinzufügen

### Falscher Stundensatz auf Rechnung
→ `clients.yaml` → `rates.remote` / `rates.onsite` prüfen

### Approver fehlt auf Timesheet
→ `clients.yaml` → `approver.name` / `approver.title` hinzufügen
