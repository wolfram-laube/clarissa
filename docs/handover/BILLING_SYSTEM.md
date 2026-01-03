# CLARISSA Billing System - Handover für neuen Chat

## 🎯 Aktueller Stand

Das Billing-System ist **funktionsfähig** nach dem GraphQL-Fix.

### Was funktioniert ✅
- Zeit tracken via GitLab `/spend` Command
- **`spent_at` Datum wird korrekt erfasst** (via GraphQL API) ✨ FIXED
- Timesheets generieren (pro Consultant)
- Konsolidierte Rechnung aus mehreren Timesheets
- CI/CD Pipeline: `.typ` → PDF → Google Drive Upload
- Google Drive Shared Drive Integration (BLAUWEISS-EDV-LLC)
- Negative Zeiteinträge (Korrekturen) werden korrekt verarbeitet

### Was noch offen ist 🔧
- Template-Validierung (Typst compile check vor Upload)
- Scheduled Pipeline am Monatsanfang (P3)
- Approval-Workflow mit Flag in .sync.json (P3)

---

## 📁 Relevante Dateien im Repo

```
gitlab.com/wolfram_laube/blauweiss_llc/irena (Project ID: 77260390)

billing/
├── config/
│   ├── clients.yaml          # Kunden, Stundensätze, Consultants, gitlab_label
│   └── sequences.yaml        # Rechnungsnummern-Zähler
├── scripts/
│   ├── generate_timesheet.py # ✅ FIXED - Nutzt GraphQL API für korrekte Datums
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

## ✅ GELÖST: Time Entry Parsing (P1)

### Das Problem (war)
Die Notes-API gab nur das Note-Erstellungsdatum zurück, nicht das `spent_at` Datum:
```python
# GitLab Note Body zeigte:
"added 8h of time spent at 2026-01-03 17:07:57 UTC"
#                         ^^^^^^^^^^^^^^^^^^^^^^
#                         Das war das NOTE-Erstellungsdatum!
```

### Die Lösung: GraphQL API
Die GraphQL API gibt `spentAt` korrekt zurück:
```graphql
query {
  project(fullPath: "wolfram_laube/blauweiss_llc/irena") {
    issues(labelName: ["client:nemensis"]) {
      nodes {
        title
        timelogs {
          nodes {
            spentAt      # ← Korrektes Datum!
            timeSpent    # ← Sekunden
            user { username }
          }
        }
      }
    }
  }
}
```

### Implementierung
`generate_timesheet.py` wurde von REST Notes API auf GraphQL umgestellt:
- `fetch_time_entries_graphql()` ersetzt `fetch_time_entries()`
- Pagination via `cursor` für große Datenmengen
- `consolidate_entries()` summiert Stunden pro Tag
- Negative Einträge (Korrekturen) werden korrekt verarbeitet

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

## 🔄 Workflow (funktioniert)

```
1. User arbeitet an Issue mit Label "client:nemensis"
2. User: /spend 4h 2026-01-15   ← Datum wird korrekt erfasst!
3. Ende Monat: generate_timesheet.py --client nemensis --all-consultants
   → Erstellt pro Consultant ein Timesheet mit korrekten Tagen ✅
4. Timesheets werden geprüft & unterschrieben
5. generate_invoice.py --client nemensis --period 2026-01
   → Liest alle Timesheets, erstellt EINE konsolidierte Rechnung
6. git push → CI → PDFs → Google Drive
```

---

## 🚀 Nächste Schritte

### P2: Edge Cases (optional)
- [ ] Was wenn `/spend` ohne Datum? → Nutzt aktuelles Datum (OK)
- [ ] Mehrere Einträge am selben Tag → Werden konsolidiert (OK)
- [ ] Zeitzone-Handling → UTC wird genutzt, lokale Zeit für Display

### P3: Automatisierung (nice-to-have)
- [ ] Scheduled Pipeline am Monatsanfang
- [ ] Notification wenn Timesheet bereit
- [ ] Approval-Flag in .sync.json

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
export GITLAB_PROJECT_PATH="wolfram_laube/blauweiss_llc/irena"
python billing/scripts/generate_timesheet.py --client nemensis --period 2026-01 --consultant wolfram

# Alle Consultants
python billing/scripts/generate_timesheet.py --client nemensis --period 2026-01 --all-consultants

# Rechnung generieren
python billing/scripts/generate_invoice.py --client nemensis --period 2026-01

# Lokal Typst kompilieren
cd billing && typst compile --root . output/2026-01_timesheet_nemensis_wolfram_de.typ
```

---

## 🧪 Test-Issues

- Issue #36: Wolfram's Zeit - `client:nemensis` Label
- Issue #37: Docker Integration - `client:nemensis` Label (hat Test-Einträge)