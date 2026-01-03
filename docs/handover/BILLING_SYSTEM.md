# CLARISSA Billing System - Handover für neuen Chat

## 🎯 Aktueller Stand

Das Billing-System ist **funktionsfähig aber noch nicht produktionsreif**.

### Was funktioniert ✅
- Zeit tracken via GitLab `/spend` Command
- Timesheets generieren (pro Consultant)
- Konsolidierte Rechnung aus mehreren Timesheets
- CI/CD Pipeline: `.typ` → PDF → Google Drive Upload
- Google Drive Shared Drive Integration (BLAUWEISS-EDV-LLC)

### Was noch nicht funktioniert ❌
- `spent_at` Datum wird von GitLab API nicht im Note-Body zurückgegeben
- Daher: Alle Zeiteinträge landen auf dem Tag des API-Calls, nicht dem echten Arbeitstag
- Username-Filter funktioniert nur wenn User selbst `/spend` eingibt (nicht via API)

---

## 📁 Relevante Dateien im Repo

```
gitlab.com/wolfram_laube/blauweiss_llc/irena (Project ID: 77260390)

billing/
├── config/
│   ├── clients.yaml          # Kunden, Stundensätze, Consultants, gitlab_label
│   └── sequences.yaml        # Rechnungsnummern-Zähler
├── scripts/
│   ├── generate_timesheet.py # Hauptscript - HAT BUGS (siehe unten)
│   ├── generate_invoice.py   # Liest .sync.json, konsolidiert, erstellt Rechnung
│   └── upload_to_drive.py    # Google Drive Upload mit Shared Drive Support
├── templates/
│   ├── timesheet.typ         # Typst Template mit Unterschriftsfeldern
│   ├── rechnung-de.typ       # Deutsche Rechnung
│   ├── invoice-en-us.typ     # US Invoice
│   └── invoice-en-eu.typ     # EU Invoice (Reverse Charge)
└── output/
    ├── *.typ                 # Generierte Dokumente
    ├── *.sync.json           # Metadaten für Invoice-Generator
    └── *.pdf                 # (nur in CI Artifacts)

.gitlab-ci.yml                # Jobs: build_invoice, upload_invoice
```

---

## 🐛 Hauptproblem: Time Entry Parsing

### Das Problem
```python
# GitLab Note Body zeigt:
"added 8h of time spent at 2026-01-03 17:07:57 UTC"
#                         ^^^^^^^^^^^^^^^^^^^^^^
#                         Das ist das NOTE-Erstellungsdatum!
#                         NICHT das spent_at Datum!
```

Wenn User `/spend 8h 2026-01-05` eingibt, speichert GitLab das `spent_at` intern, aber die Notes-API gibt es nicht zurück.

### Mögliche Lösungen
1. **Timelogs API** - `GET /projects/:id/issues/:iid/timelogs` (eventuell nur Premium?)
2. **User Time Logs** - `GET /users/:id/timelogs` 
3. **GraphQL API** - Könnte mehr Details liefern
4. **Workaround:** Issue-Title als "Bucket" nutzen, Datum aus Title parsen

### Test-Issues
- Issue #36: Wolfram's Zeit (6h)
- Issue #37: Ian's Zeit (20h) - Hat kaputte Einträge vom Testen

---

## 🔧 clients.yaml Struktur

```yaml
consultants:
  wolfram:
    name: "Wolfram Laube"
    gitlab_username: "wolfram.laube"  # ACHTUNG: Punkt, nicht Unterstrich!
  ian:
    name: "Ian Matejka"
    gitlab_username: "ian.matejka"

clients:
  nemensis:
    name: "nemensis AG Deutschland"
    gitlab_label: "client:nemensis"   # Issues mit diesem Label = nemensis Zeit
    rates:
      remote: 105
      onsite: 120
    consultants:
      - wolfram
      - ian
    approver:
      name: "Max Mustermann"
      title: "Projektleiter"
```

---

## 🔄 Gewünschter Flow (Ziel)

```
1. User arbeitet an Issue mit Label "client:nemensis"
2. User: /spend 4h 2026-01-15
3. Ende Monat: generate_timesheet.py --client nemensis --all-consultants
   → Erstellt pro Consultant ein Timesheet mit korrekten Tagen
4. Timesheets werden geprüft & unterschrieben
5. generate_invoice.py --client nemensis --period 2026-01
   → Liest alle Timesheets, erstellt EINE konsolidierte Rechnung
6. git push → CI → PDFs → Google Drive
```

---

## 🚀 Nächste Schritte (Priorität)

### P1: Time Entry Parsing fixen
- GitLab Timelogs API testen
- Oder GraphQL API probieren
- `generate_timesheet.py` entsprechend anpassen

### P2: Edge Cases
- Was wenn `/spend` ohne Datum?
- Negative Zeit (Korrekturen)?
- Mehrere Einträge am selben Tag konsolidieren

### P3: Automatisierung
- Scheduled Pipeline am Monatsanfang
- Notification wenn Timesheet bereit
- Approval-Flag in .sync.json

---

## 🔑 Credentials (für neuen Chat)

```
GitLab Project: 77260390
GitLab PAT: glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt

Google Drive Folder: 1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs
Service Account: claude-assistant@myk8sproject-207017.iam.gserviceaccount.com
```

---

## 📋 Test-Kommandos

```bash
# Timesheet generieren
export GITLAB_TOKEN="glpat-xxx"
python billing/scripts/generate_timesheet.py --client nemensis --period 2026-01 --consultant wolfram

# Alle Consultants
python billing/scripts/generate_timesheet.py --client nemensis --period 2026-01 --all-consultants

# Rechnung generieren
python billing/scripts/generate_invoice.py --client nemensis --period 2026-01

# Lokal Typst kompilieren
cd billing && typst compile --root . output/2026-01_timesheet_nemensis_wolfram_de.typ
```
