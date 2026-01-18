# Contributing to CLARISSA

Willkommen! Dieses Dokument beschreibt den kompletten Entwicklungsworkflow für CLARISSA.

> 📖 **Quick Reference:** [Workflow-Cheatsheet](docs/guides/contributing/cheatsheet.md)  
> 🏗️ **Architektur-Entscheidung:** [ADR-001](docs/architecture/decisions/ADR-001_GitLab-PM-Workflow.md)

---

## Inhaltsverzeichnis

1. [Workflow-Übersicht](#workflow-übersicht)
2. [Schritt-für-Schritt Anleitung](#schritt-für-schritt-anleitung)
3. [Label-System](#label-system)
4. [Milestones](#milestones)
5. [Issue Board](#issue-board)
6. [Conventional Commits](#conventional-commits)
7. [Best Practices](#best-practices)

---

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
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                      │
│                        main                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Kernprinzipien

| Prinzip | Beschreibung |
|---------|--------------|
| **Issue-First** | Jede Arbeit beginnt mit einem Issue |
| **Branch per Issue** | Ein Feature-Branch pro Issue |
| **Kein Push auf main** | Alle Änderungen via Merge Request |
| **CI-Gate** | Pipeline muss grün sein vor Merge |
| **Auto-Close** | `Closes #X` im Commit schließt Issue |

---

## Schritt-für-Schritt Anleitung

### 1️⃣ Issue erstellen

```markdown
Title: "feat: Implement feature X"
Labels: type::feature, component::*, priority::*, workflow::backlog
Milestone: v0.2 (optional)
```

➡️ [Issue Templates](.gitlab/issue_templates/) nutzen!

### 2️⃣ Feature-Branch erstellen

```bash
git checkout main && git pull
git checkout -b feature/43-complete-pm-docs
#                 ↑      ↑
#            Prefix   Issue-ID + Slug
```

**Branch-Prefixe:**
| Prefix | Verwendung |
|--------|------------|
| `feature/` | Neue Features |
| `fix/` | Bugfixes |
| `docs/` | Reine Dokumentation |
| `chore/` | Maintenance, Refactoring |

### 3️⃣ Issue-Status aktualisieren

Label ändern: `workflow::backlog` → `workflow::in-progress`

### 4️⃣ Entwickeln & Committen

```bash
git commit -m "feat(tutorials): add notebook 07 - RL Agent"
git commit -m "fix(ci): correct docker image tag"
```

Siehe [Conventional Commits](#conventional-commits) für Details.

### 5️⃣ Letzter Commit mit Auto-Close

```bash
git commit -m "docs: add project management guide

Closes #43"
```

### 6️⃣ Push & MR erstellen

```bash
git push -u origin feature/43-complete-pm-docs
```

MR erstellen mit:
- ✅ Title wie Hauptcommit
- ✅ `Closes #43` in Description
- ✅ Gleiche Labels wie Issue
- ✅ "Remove source branch" aktiviert

### 7️⃣ Pipeline & Merge

- Pipeline abwarten (muss grün sein!)
- `docs:preview` manuell triggern bei Docs
- Nach Erfolg: Merge
- Issue wird automatisch geschlossen

---

## Label-System

CLARISSA verwendet **Scoped Labels** (`scope::value`) für konsistente Kategorisierung.

### Type Labels (`type::`)

| Label | Farbe | Verwendung |
|-------|-------|------------|
| `type::feature` | 🟢 `#428BCA` | Neue Funktionalität |
| `type::bug` | 🔴 `#D73A4A` | Fehlerbehebung |
| `type::documentation` | ⚪ `#CCCCCC` | Dokumentation |
| `type::chore` | 🟤 `#795548` | Maintenance, Refactoring |
| `type::research` | 🟣 `#9C27B0` | Spikes, Untersuchungen |
| `type::adr` | 🔵 `#00BCD4` | Architecture Decision Record |
| `type::task` | 🔵 `#1E88E5` | Allgemeine Aufgaben |
| `type::fix` | 🟠 `#FB8C00` | Kleine Fixes |

### Priority Labels (`priority::`)

| Label | Farbe | Bedeutung |
|-------|-------|-----------|
| `priority::critical` | 🔴 `#B71C1C` | Alles stehen lassen! |
| `priority::high` | 🟠 `#E65100` | Diese Woche |
| `priority::medium` | 🟡 `#FDD835` | Dieser Sprint |
| `priority::low` | 🔵 `#64B5F6` | Wenn Zeit ist |

### Component Labels (`component::`)

| Label | Bereich |
|-------|---------|
| `component::nlp-agent` | NLP/Conversational Interface |
| `component::simulator` | OPM Flow, ECLIPSE Adapter |
| `component::governance` | Constraint Engine, Validation |
| `component::learning` | RL Agent, Feedback Loop |
| `component::infrastructure` | CI/CD, Docker, K8s |
| `component::documentation` | Docs, Guides, ADRs |
| `component::data-mesh` | Knowledge Layer, Vector DB |
| `component::api` | REST API |
| `component::tutorials` | Jupyter Notebooks |
| `component::paper` | Wissenschaftliche Publikationen |
| `component::ci` | CI/CD Pipeline |

### Workflow Labels (`workflow::`)

| Label | Board-Spalte | Bedeutung |
|-------|--------------|-----------|
| `workflow::backlog` | Backlog | Noch nicht geplant |
| `workflow::ready` | Ready | Bereit zum Start |
| `workflow::in-progress` | In Progress | In Bearbeitung |
| `workflow::review` | Review | MR offen |
| `workflow::blocked` | Blocked | Wartet auf Abhängigkeit |

### Spezielle Labels

| Label | Verwendung |
|-------|------------|
| `good-first-issue` | Einsteigerfreundlich |
| `help-wanted` | Hilfe gesucht |
| `needs-discussion` | Team-Diskussion nötig |
| `wontfix` | Wird nicht umgesetzt |
| `duplicate` | Duplikat eines anderen Issues |

---

## Milestones

Milestones repräsentieren Release-Versionen:

| Milestone | Fokus | Ziel |
|-----------|-------|------|
| **v0.1 - Foundation** | Architektur, CI/CD Baseline | Grundgerüst |
| **v0.2 - SPE Europe Draft** | Paper, OPM Integration | Konferenz-Submission |
| **v0.3 - NLP Pipeline** | Conversation Layer, Intent | MVP NLP |
| **v0.4 - ECLIPSE Parser** | Deck Parsing, Validation | Parser fertig |
| **v1.0 - Production** | Vollständige Integration | Erster Release |

---

## Issue Board

Das [Kanban Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) visualisiert den Workflow:

```
┌──────────┬──────────┬─────────────┬──────────┬──────────┐
│ Backlog  │  Ready   │ In Progress │  Review  │ Blocked  │
├──────────┼──────────┼─────────────┼──────────┼──────────┤
│ workflow │ workflow │  workflow   │ workflow │ workflow │
│ ::backlog│ ::ready  │ ::in-prog.  │ ::review │ ::blocked│
├──────────┼──────────┼─────────────┼──────────┼──────────┤
│ #50      │ #48      │ #43 ← Du    │ #41      │ #35      │
│ #51      │ #49      │ #44         │          │          │
│ ...      │          │             │          │          │
└──────────┴──────────┴─────────────┴──────────┴──────────┘
```

**Workflow:**
1. Neues Issue → `workflow::backlog`
2. Sprint-Planung → `workflow::ready`
3. Arbeit beginnt → `workflow::in-progress`
4. MR erstellt → `workflow::review`
5. Merge → Issue geschlossen (verschwindet vom Board)

---

## Conventional Commits

Format: `<type>(<scope>): <description>`

### Typen

| Typ | Verwendung | Beispiel |
|-----|------------|----------|
| `feat` | Neues Feature | `feat(api): add REST endpoint` |
| `fix` | Bugfix | `fix(parser): handle empty deck` |
| `docs` | Dokumentation | `docs: update README` |
| `chore` | Maintenance | `chore: update dependencies` |
| `refactor` | Refactoring | `refactor(core): simplify logic` |
| `test` | Tests | `test: add unit tests for parser` |
| `ci` | CI/CD | `ci: fix docker build` |
| `style` | Formatting | `style: fix indentation` |
| `perf` | Performance | `perf: optimize query` |

### Scope (optional)

Der Scope entspricht oft dem Component-Label:
- `feat(tutorials):` → `component::tutorials`
- `fix(ci):` → `component::ci`
- `docs(api):` → `component::api`

### Auto-Close Keywords

Im Commit-Body oder MR-Description:
- `Closes #43`
- `Fixes #43`
- `Resolves #43`

---

## Best Practices

### ✅ DO

- Kleine, fokussierte MRs (< 500 Zeilen)
- Aussagekräftige Commit-Messages
- Issue vor Arbeitsbeginn erstellen
- Labels konsequent setzen
- Pipeline-Erfolg vor Merge
- ADRs für architekturelle Entscheidungen
- Branch nach Merge löschen

### ❌ DON'T

- Direkt auf `main` pushen
- Große, monolithische MRs
- Commits ohne Kontext (`fix`, `update`, `asdf`)
- MR mergen bei roter Pipeline
- Ungetesteten Code mergen
- Labels vergessen

---

## Ressourcen

| Link | Beschreibung |
|------|--------------|
| [Issue Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) | Kanban Board |
| [All Issues](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues) | Issue-Liste |
| [Merge Requests](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/merge_requests) | Offene MRs |
| [Pipelines](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines) | CI/CD Status |
| [ADR-001](docs/architecture/decisions/ADR-001_GitLab-PM-Workflow.md) | Workflow-Entscheidung |
| [Cheatsheet](docs/guides/contributing/cheatsheet.md) | Quick Reference |

---

*Diese Dokumentation folgt dem dokumentierten Workflow (Issue #43 → MR).*
