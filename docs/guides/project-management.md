# Project Management Guide

Dieses Dokument beschreibt das vollständige Projektmanagement-Setup für CLARISSA in GitLab.

> 🏗️ **Architektur-Entscheidung:** [ADR-018](../architecture/adr/ADR-018-gitlab-pm-workflow.md)  
> 📖 **Workflow:** [CONTRIBUTING.md](../contributing.md)

---

## Übersicht

CLARISSA verwendet GitLab als **Single Source of Truth** für:

| Bereich | GitLab Feature |
|---------|----------------|
| Issue Tracking | Issues |
| Größere Initiativen | Epics (via Issue-Links) |
| Sprint-Planung | Milestones |
| Aufgaben-Visualisierung | Issue Board |
| Code Review | Merge Requests |
| Automatisierung | CI/CD Pipelines |
| Dokumentation | Repository + GitLab Pages |

---

## Label-Taxonomie

### Scoped Labels

GitLab **Scoped Labels** (`scope::value`) garantieren, dass nur ein Label pro Scope aktiv ist:

```
type::feature + type::bug  → Nicht möglich ✗
type::feature              → OK ✓
```

### Vollständige Label-Referenz

#### `type::` - Art der Arbeit

| Label | Hex-Farbe | Beschreibung |
|-------|-----------|--------------|
| `type::feature` | `#428BCA` | Neue Funktionalität |
| `type::bug` | `#D73A4A` | Fehlerbehebung |
| `type::documentation` | `#CCCCCC` | Dokumentation |
| `type::chore` | `#795548` | Maintenance |
| `type::research` | `#9C27B0` | Spikes, Untersuchungen |
| `type::adr` | `#00BCD4` | Architecture Decision Record |
| `type::task` | `#1E88E5` | Allgemeine Aufgaben |
| `type::fix` | `#FB8C00` | Kleine Fixes |

#### `priority::` - Dringlichkeit

| Label | Hex-Farbe | SLA |
|-------|-----------|-----|
| `priority::critical` | `#B71C1C` | Sofort (< 24h) |
| `priority::high` | `#E65100` | Diese Woche |
| `priority::medium` | `#FDD835` | Dieser Sprint (2 Wochen) |
| `priority::low` | `#64B5F6` | Backlog |

#### `component::` - Systembereich

| Label | Architektur-Komponente |
|-------|------------------------|
| `component::nlp-agent` | Conversational Interface, Intent Classification |
| `component::simulator` | OPM Flow, ECLIPSE Adapter |
| `component::governance` | Constraint Engine, Validation Layer |
| `component::learning` | RL Agent, Feedback Loop |
| `component::infrastructure` | Docker, Kubernetes, CI/CD |
| `component::documentation` | Docs, Guides, ADRs |
| `component::data-mesh` | Knowledge Layer, Vector DB, RAG |
| `component::api` | REST API, Endpoints |
| `component::tutorials` | Jupyter Notebooks |
| `component::paper` | Wissenschaftliche Publikationen |
| `component::ci` | GitLab CI/CD Pipeline |

#### `workflow::` - Arbeits-Status

| Label | Board-Spalte | Trigger |
|-------|--------------|---------|
| `workflow::backlog` | Backlog | Issue erstellt |
| `workflow::ready` | Ready | Sprint-Planung |
| `workflow::in-progress` | In Progress | Arbeit beginnt |
| `workflow::review` | Review | MR erstellt |
| `workflow::blocked` | Blocked | Abhängigkeit fehlt |

#### Spezielle Labels (nicht-scoped)

| Label | Verwendung |
|-------|------------|
| `good-first-issue` | Einsteigerfreundlich, gut dokumentiert |
| `help-wanted` | Externe Hilfe willkommen |
| `needs-discussion` | Team-Entscheidung erforderlich |
| `wontfix` | Bewusst nicht umgesetzt |
| `duplicate` | Verweis auf Original-Issue |
| `client:nemensis` | Kunde/Projekt-spezifisch |

---

## Milestones

### Release-Struktur

```
v0.1 - Foundation
  │
  ├── v0.2 - SPE Europe Draft
  │     │
  │     └── v0.3 - NLP Pipeline
  │           │
  │           └── v0.4 - ECLIPSE Parser
  │                 │
  │                 └── v1.0 - Production
```

### Milestone-Details

| Milestone | Fokus | Key Results |
|-----------|-------|-------------|
| **v0.1 - Foundation** | Grundgerüst | CI/CD ✅, Architektur ✅, Runner-Matrix ✅ |
| **v0.2 - SPE Europe Draft** | Konferenz | Paper-Draft, OPM Integration, Tutorials |
| **v0.3 - NLP Pipeline** | Conversation | Intent Classification, Entity Extraction |
| **v0.4 - ECLIPSE Parser** | Deck Handling | Parser, Validator, Generator |
| **v1.0 - Production** | Release | Full Integration, Testing, Docs |

### Milestone-Nutzung

1. **Issue erstellen** → Milestone zuweisen
2. **Burndown** automatisch in GitLab
3. **Milestone schließen** wenn alle Issues done

---

## Issue Board

### Board-Konfiguration

Das [CLARISSA Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) hat folgende Listen:

| Liste | Scope | Filter |
|-------|-------|--------|
| **Open** | Alle | Kein `workflow::` Label |
| **Backlog** | Geplant | `workflow::backlog` |
| **Ready** | Sprint | `workflow::ready` |
| **In Progress** | Aktiv | `workflow::in-progress` |
| **Review** | MR offen | `workflow::review` |
| **Blocked** | Wartend | `workflow::blocked` |

### Board-Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌──────┐    ┌─────────┐    ┌───────┐    ┌────────┐    ┌────┐ │
│  │ Open │ →  │ Backlog │ →  │ Ready │ →  │In Prog.│ →  │Rev.│ │
│  └──────┘    └─────────┘    └───────┘    └────────┘    └──┬─┘ │
│                                              ↑            │   │
│                                              │            ▼   │
│                                         ┌────────┐    ┌──────┐│
│                                         │Blocked │    │Merged││
│                                         └────────┘    └──────┘│
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Drag & Drop

- Issue von **Backlog** → **Ready** = Sprint-Planung
- Issue von **Ready** → **In Progress** = Arbeit beginnt
- Label wird automatisch aktualisiert!

---

## Epics

Da GitLab Free keine echten Epics hat, nutzen wir **Issues als Epics**:

### Epic-Issue erstellen

```markdown
Title: "Epic: Interactive Tutorial Series"
Labels: type::feature, priority::high

Description:
## Objectives
- 10 Jupyter Notebooks
- GitPod/Colab Support

## Child Issues
- #38 Notebooks 01-03
- #40 Notebooks 04-06  
- #41 Notebooks 07-10

## Acceptance Criteria
- [ ] All notebooks executable
- [ ] MkDocs renders correctly
```

### Child-Issues verlinken

In jedem Child-Issue:
```markdown
Relates to #39
Part of Epic #39
```

---

## Issue Templates

Verfügbare Templates in `.gitlab/issue_templates/`:

| Template | Verwendung |
|----------|------------|
| `adr.md` | Architecture Decision Record |
| `bug.md` | Bug Report |
| `feature.md` | Feature Request |

### Template nutzen

1. New Issue → Choose a template
2. Felder ausfüllen
3. Labels/Milestone setzen
4. Submit

---

## Metriken

### Velocity Tracking

- **Issues closed per Milestone** = Velocity
- **Burndown Chart** in Milestone-Ansicht
- **Time Tracking** via `/spend 2h` Commands

### Label-Statistiken

```
GitLab → Issues → Labels → Klick auf Label → Issue-Count
```

---

## Integration mit CI/CD

### Auto-Close via MR

```yaml
# .gitlab-ci.yml ist bereits konfiguriert
# MR-Merge → Issue auto-close wenn:
# - "Closes #X" im Commit
# - "Fixes #X" im MR-Description
```

### Pipeline-Status im Board

- 🟢 Pipeline grün → MR kann gemerged werden
- 🔴 Pipeline rot → Fix erforderlich

---

## Referenzen

- [GitLab Issue Management](https://docs.gitlab.com/ee/user/project/issues/)
- [GitLab Boards](https://docs.gitlab.com/ee/user/project/issue_board.html)
- [Scoped Labels](https://docs.gitlab.com/ee/user/project/labels.html#scoped-labels)
- [ADR-018](../architecture/adr/ADR-018-gitlab-pm-workflow.md)

---

*Erstellt als Teil von Issue #43*
