# Contributing to CLARISSA

Dieses Dokument beschreibt den Entwicklungsworkflow für CLARISSA.

## Workflow-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                         EPIC                                     │
│  (Große Initiative, überspannt mehrere Milestones)              │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                   │
│         ▼                 ▼                 ▼                   │
│     ┌───────┐         ┌───────┐         ┌───────┐              │
│     │Issue 1│         │Issue 2│         │Issue 3│              │
│     └───┬───┘         └───┬───┘         └───┬───┘              │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│    feature/1-x       feature/2-y       feature/3-z             │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│       MR !1             MR !2             MR !3                 │
│         │                 │                 │                   │
│         └────────────────►├◄────────────────┘                   │
│                           ▼                                      │
│                        main                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Schritt-für-Schritt Anleitung

### 1. Issue erstellen

Jede Arbeit beginnt mit einem Issue:

```bash
# Via GitLab UI oder API
Title: "feat: Implement feature X"
Labels: component::*, type::*, priority::*, workflow::backlog
```

**Issue-Typen:**
- `type::feature` - Neue Funktionalität
- `type::bug` - Fehlerbehebung
- `type::documentation` - Dokumentation
- `type::chore` - Maintenance, Refactoring

**Workflow-Labels:**
- `workflow::backlog` - Noch nicht begonnen
- `workflow::in-progress` - In Bearbeitung
- `workflow::review` - Im Review
- `workflow::done` - Abgeschlossen (auto via MR-Merge)

### 2. Feature-Branch erstellen

```bash
# Branch-Naming: feature/{issue-id}-{kurzbeschreibung}
git checkout main
git pull origin main
git checkout -b feature/42-gitlab-pm-workflow-docs
```

**Branch-Prefixe:**
- `feature/` - Neue Features
- `fix/` - Bugfixes
- `docs/` - Reine Dokumentation
- `chore/` - Maintenance

### 3. Issue-Status aktualisieren

Label ändern: `workflow::backlog` → `workflow::in-progress`

### 4. Entwickeln & Committen

```bash
# Conventional Commits Format
git commit -m "feat(tutorials): add notebook 07 - RL Agent"
git commit -m "fix(ci): correct docker image tag"
git commit -m "docs: update README with setup instructions"
```

**Commit-Prefixe:**
| Prefix | Verwendung |
|--------|------------|
| `feat:` | Neues Feature |
| `fix:` | Bugfix |
| `docs:` | Dokumentation |
| `chore:` | Maintenance |
| `refactor:` | Code-Refactoring |
| `test:` | Tests hinzufügen/ändern |
| `ci:` | CI/CD Änderungen |

**Scope (optional):** `feat(tutorials):`, `fix(ci):`

### 5. Letzter Commit mit Auto-Close

```bash
# Der letzte Commit schließt das Issue automatisch
git commit -m "docs: add CONTRIBUTING.md

Closes #42"
```

**Auto-Close Keywords:**
- `Closes #42`
- `Fixes #42`
- `Resolves #42`

### 6. Push & MR erstellen

```bash
git push -u origin feature/42-gitlab-pm-workflow-docs
```

MR erstellen mit:
- **Title:** Wie Hauptcommit (z.B. "docs: Document GitLab PM Workflow")
- **Description:** Summary + `Closes #42`
- **Labels:** Gleiche wie Issue
- **Remove source branch:** ✅ Aktiviert

### 7. CI-Pipeline abwarten

- Pipeline muss erfolgreich sein
- Bei Fehlern: Fixen und neu pushen
- `docs:preview` Job manuell triggern bei Dokumentations-MRs

### 8. Merge

Nach erfolgreicher Pipeline:
- MR mergen (Squash optional)
- Issue wird automatisch geschlossen
- Source-Branch wird gelöscht

## Epics

Für größere Initiativen, die mehrere Issues umfassen:

```markdown
# Epic erstellen
Title: "feat(tutorials): Interactive Jupyter Tutorial Series"
Description: 
  - Überblick über die Initiative
  - Liste der Child-Issues
  - Akzeptanzkriterien für das Gesamtziel

# Child-Issues verlinken
"Relates to #39" oder "Part of Epic #39" in Issue-Description
```

## Labels

### Component Labels (`component::*`)
- `component::core` - Kernfunktionalität
- `component::tutorials` - Tutorial-Notebooks
- `component::documentation` - Allgemeine Docs
- `component::ci-cd` - Pipeline & Automation

### Priority Labels (`priority::*`)
- `priority::critical` - Sofort
- `priority::high` - Diese Woche
- `priority::medium` - Dieser Sprint
- `priority::low` - Backlog

## Best Practices

### DO ✅
- Kleine, fokussierte MRs (< 500 Zeilen)
- Aussagekräftige Commit-Messages
- Issue vor Arbeitsbeginn erstellen
- Pipeline-Erfolg vor Merge prüfen
- ADRs für architekturelle Entscheidungen

### DON'T ❌
- Direkt auf `main` pushen
- Große, monolithische MRs
- Commits ohne Kontext ("fix", "update")
- MR mergen bei fehlgeschlagener Pipeline
- Ungetesteten Code mergen

## Beispiel: Kompletter Workflow

```bash
# 1. Issue #42 existiert bereits

# 2. Branch erstellen
git checkout -b feature/42-gitlab-pm-workflow-docs

# 3. Entwickeln
vim docs/architecture/decisions/ADR-001.md
vim CONTRIBUTING.md

# 4. Committen
git add .
git commit -m "docs: add ADR-001 GitLab PM Workflow"
git commit -m "docs: add CONTRIBUTING.md

Closes #42"

# 5. Pushen
git push -u origin feature/42-gitlab-pm-workflow-docs

# 6. MR erstellen (via UI oder API)
# 7. Pipeline abwarten
# 8. Mergen → Issue #42 wird automatisch geschlossen
```

## ADR (Architecture Decision Records)

Für wichtige technische Entscheidungen:

```
docs/architecture/decisions/
├── ADR-001_GitLab-PM-Workflow.md
├── ADR-002_OPM-Flow-Integration.md
└── ...
```

**ADR-Format:**
- Status (Proposed/Accepted/Deprecated)
- Context (Warum diese Entscheidung?)
- Decision (Was wurde entschieden?)
- Consequences (Auswirkungen)

Siehe [ADR-001](docs/architecture/decisions/ADR-001_GitLab-PM-Workflow.md) als Beispiel.

---

*Diese Dokumentation wurde erstellt unter Einhaltung des dokumentierten Workflows (Issue #42 → MR).*
