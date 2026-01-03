# 💰 Rechnungs-Workflow - Schritt für Schritt

> **TL;DR:** Zeit in GitLab tracken → Timesheet generieren → Prüfen → Rechnung erstellen → Automatisch in Google Drive

---

## 🎯 Übersicht

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  1. ZEIT TRACKEN        2. TIMESHEET           3. RECHNUNG        │
│  ────────────────       ──────────────         ─────────────      │
│                                                                    │
│  GitLab Issues    →    Timesheet.typ    →    Rechnung.pdf         │
│  /spend 4h             (editierbar)          + Timesheet.pdf      │
│                              │                      │              │
│                              ▼                      ▼              │
│                        [prüfen/korr.]        Google Drive         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Schritt 1: Zeit tracken (täglich)

In **jedem GitLab Issue** das du bearbeitest:

```
/spend 4h                    # 4 Stunden heute
/spend 2h 2026-01-15         # 2 Stunden am 15. Januar
/spend 30m                   # 30 Minuten
```

**💡 Tipps:**
- Mach das am Ende jedes Arbeitstages
- Lieber zu viel als zu wenig dokumentieren
- Das Issue sollte zur Tätigkeit passen (für die Beschreibung im Timesheet)

---

## 📋 Schritt 2: Timesheet generieren (Ende des Monats)

### Option A: Automatisch aus GitLab

```bash
cd clarissa

# Timesheet für Januar 2026, Client "nemensis", auf Deutsch
python billing/scripts/generate_timesheet.py \
    --client nemensis \
    --period 2026-01 \
    --lang de
```

**Output:**
- `billing/output/2026-01_timesheet_nemensis_de.typ` (Quelldatei)
- `billing/output/2026-01_timesheet_nemensis_de.pdf` (PDF)
- `billing/output/2026-01_timesheet_nemensis_de.sync.json` (für Sync)

### Option B: Manuell erstellen

Kopiere das Template und passe die Daten an:

```bash
cp billing/templates/timesheet.typ billing/output/2026-01_timesheet_nemensis_de.typ
```

Dann editieren:
```typst
#timesheet(
  year: 2026,
  month: 1,
  client_name: "nemensis AG Deutschland",
  ...
  daily_entries: (
    "2": (8, "Architecture Review"),
    "5": (6, "API Development"),
    ...
  ),
)
```

---

## 📋 Schritt 3: Timesheet prüfen & korrigieren

**Öffne das Timesheet:**
```bash
open billing/output/2026-01_timesheet_nemensis_de.pdf
```

**Checklist:**
- [ ] Sind alle Arbeitstage erfasst?
- [ ] Stimmen die Stunden?
- [ ] Sind die Beschreibungen korrekt?
- [ ] Wurden Feiertage/Urlaub berücksichtigt?

**Korrigieren:**

Editiere die `.typ` Datei:
```bash
vim billing/output/2026-01_timesheet_nemensis_de.typ
```

Änderungen zurück zu GitLab syncen (optional):
```bash
python billing/scripts/sync_timesheet.py \
    billing/output/2026-01_timesheet_nemensis_de.typ
```

---

## 📋 Schritt 4: Rechnung generieren

```bash
python billing/scripts/generate_invoice.py \
    --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ
```

**Output:**
- `billing/output/AR_001_2026_nemensis.typ`
- `billing/output/AR_001_2026_nemensis.pdf`

---

## 📋 Schritt 5: Commit & Upload

### Manuell (lokal):
```bash
python billing/scripts/generate_invoice.py \
    --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ \
    --upload
```

### Automatisch (CI Pipeline):
```bash
git add billing/output/
git commit -m "billing: add January 2026 timesheet for nemensis"
git push
```

Die Pipeline macht automatisch:
1. ✅ `build_invoice` - Kompiliert alle `.typ` zu PDF
2. ✅ `upload_invoice` - Lädt PDFs zu Google Drive hoch

---

## 📁 Google Drive Struktur

```
BlauWeiss LLC/Finance/Invoices/
└── 2026/
    ├── 01_nemensis/
    │   ├── 2026-01_timesheet_nemensis_de.pdf
    │   └── AR_001_2026_nemensis.pdf
    ├── 02_nemensis/
    │   └── ...
    └── 01_oxy/
        └── ...
```

🔗 **Link:** https://drive.google.com/drive/folders/1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs

---

## 🔧 Konfiguration

### Neuen Client hinzufügen

Editiere `billing/config/clients.yaml`:

```yaml
clients:
  newclient:
    name: "New Client GmbH"
    short: "NC"
    template: "rechnung-de"    # oder: invoice-en-us, invoice-en-eu
    currency: "EUR"            # oder: USD
    address:
      line1: "Hauptstraße 1"
      city: "D - 10115 Berlin"
    vat_id: "DE123456789"
    contract_number: "00003154"
    rates:
      remote: 105
      onsite: 120
```

### Verfügbare Templates

| Template | Sprache | Währung | MwSt |
|----------|---------|---------|------|
| `invoice-en-us.typ` | Englisch | USD | Keine |
| `invoice-en-eu.typ` | Englisch | EUR | Reverse Charge |
| `rechnung-de.typ` | Deutsch | EUR | Reverse Charge |

### Timesheet-Sprachen

| Code | Sprache |
|------|---------|
| `de` | Deutsch |
| `en` | English |
| `vi` | Tiếng Việt |
| `ar` | العربية |
| `is` | Íslenska |

---

## ⚡ Quick Reference

```bash
# === MONATLICHER WORKFLOW ===

# 1. Timesheet aus GitLab generieren
python billing/scripts/generate_timesheet.py -c nemensis -p 2026-01 --lang de

# 2. Prüfen
open billing/output/2026-01_timesheet_nemensis_de.pdf

# 3. (Optional) Korrekturen syncen
python billing/scripts/sync_timesheet.py billing/output/2026-01_timesheet_nemensis_de.typ

# 4. Rechnung generieren
python billing/scripts/generate_invoice.py --from-timesheet billing/output/2026-01_timesheet_nemensis_de.typ

# 5. Commit → CI macht den Rest
git add billing/output/ && git commit -m "billing: Januar 2026 nemensis" && git push


# === MANUELLE UPLOADS ===

# Einzelne Datei hochladen
python billing/scripts/upload_to_drive.py --folder "2026/01_nemensis" invoice.pdf

# Mit --upload Flag
python billing/scripts/generate_invoice.py --from-timesheet timesheet.typ --upload
```

---

## 🆘 Troubleshooting

### "No time entries found"
→ Hast du `/spend` in GitLab Issues verwendet?

### "Unknown client"
→ Füge den Client in `billing/config/clients.yaml` hinzu

### Upload fehlgeschlagen
→ Prüfe ob `GOOGLE_SERVICE_ACCOUNT_KEY` in GitLab CI Variables gesetzt ist

### PDF sieht komisch aus
→ Prüfe ob Poppins Font installiert ist (CI macht das automatisch)

---

## 📞 Support

Bei Fragen: GitLab Issue erstellen oder Wolfram fragen 😄
