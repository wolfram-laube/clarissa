# HANDOVER: Operations Portal — 02.02.2026

## Session Summary

CRM-System vollständig migriert, QA-Automation implementiert, Operations Portal deployed.

## ⚠️ ERSTE AUFGABE NÄCHSTE SESSION: Naming Fix

**Problem:**
- Pages URL: `irena-40cc50.gitlab.io` (alter Projektname aus ECLIPSE-Zeit)
- Portal/Docs Title: "CLARISSA Documentation" (Forschungsprojekt)
- Soll sein: "Blauweiss EDV" oder "Blauweiss Operations"

**Fix-Optionen:**
1. GitLab Pages Custom Domain einrichten (z.B. `ops.blauweiss-edv.at`)
2. Projekt umbenennen → neue Pages URL
3. Mindestens: mkdocs.yml `site_name` ändern + Portal Titles anpassen

**Betroffene Dateien:**
- `mkdocs.yml` → `site_name: "Blauweiss Operations"`
- `docs/portal.html` → Title + Branding
- `docs/index.md` → Header/Intro
- Alle `<title>` Tags in HTML-Seiten

---

## Was wurde erledigt

### 1. CRM System (✅ KOMPLETT)
- 185 Issues aus CSV migriert
- 8-Spalten Kanban Board
- 44 Group-Level Labels
- 2 Duplikate bereinigt
- Board: https://gitlab.com/wolfram_laube/blauweiss_llc/ops/crm/-/boards/10081703

### 2. QA Automation (✅ KOMPLETT)
- `scripts/ci/crm_integrity_check.py` — 13 Checks
- `scripts/ci/applications_qa.py` — Pipeline-Validierung + CRM-Dedup
- Weekly Schedule #4125129: Mo 07:00 Vienna

### 3. Operations Portal (✅ KOMPLETT)
- `docs/portal.html` — Zentrale Steuerung
- `docs/ops/quickstart.md` — Bedienungsanleitung
- `docs/ops/crm.md` — CRM Dokumentation
- `docs/ops/api-reference.md` — API Reference

### 4. Schedules
- #4094512: Monthly Billing (1. 06:00) — AKTIV
- #4125129: CRM Integrity (Mo 07:00) — AKTIV
- #4125172: Applications Pipeline (Mo-Fr 08:00) — INAKTIV

### 5. GitHub Sync (✅ FUNKTIONIERT)

## Live URLs (mit falschem Naming)

| Page | URL |
|------|-----|
| Portal | https://irena-40cc50.gitlab.io/portal.html |
| Quick Start | https://irena-40cc50.gitlab.io/ops/quickstart/ |
| CRM Board | https://gitlab.com/wolfram_laube/blauweiss_llc/ops/crm/-/boards/10081703 |

## Offene Aufgaben (Priorisiert)

### P0: Naming Fix
- [ ] Entscheidung: Custom Domain oder Projekt umbenennen?
- [ ] mkdocs.yml site_name ändern
- [ ] Portal Branding anpassen
- [ ] Index.md Header anpassen

### P1: Funktional
- [ ] Applications Schedule aktivieren (#4125172)
- [ ] CRM Issues mit freelancermap URLs verlinken
- [ ] Billing Pipeline prüfen (billing.yml fehlt)

### P2: Polish
- [ ] Weitere Trigger Pages (match, drafts, crm-integrity)
- [ ] Portal Live-Daten (CORS-Proxy)
- [ ] Echten Trigger Token einsetzen

## Wichtige IDs

| Resource | ID |
|----------|-----|
| CLARISSA Project | 77260390 |
| CRM Project | 78171527 |
| Group | 120698013 |
| CRM Board | 10081703 |
| Applications Schedule | #4125172 |

## Commits dieser Session

```
d0dcae2f  docs: add handover document
65957a54  docs: add Quick Start, API Reference and Portal to navigation
626d3cca  feat: add Operations Portal Dashboard
fe9cb8df  docs: add Operations section with CRM docs
6509d438  feat: implement QA validation scripts
```
