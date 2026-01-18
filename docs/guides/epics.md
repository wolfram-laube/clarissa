# Epics in GitLab Free Tier

Da GitLab Free keine echten Epics unterstützt, nutzen wir **Issues als Epics** mit einem strukturierten Pattern.

> 💡 **Beispiel:** [Epic #39 - CLARISSA Tutorial System](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues/39)

---

## Warum Epics?

Epics gruppieren zusammengehörige Issues zu einer größeren Initiative:

```
┌────────────────────────────────────────────────────────┐
│                    EPIC #39                            │
│         "CLARISSA Tutorial System"                     │
│                                                        │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│   │ #38     │    │ #40     │    │ #41     │          │
│   │Notebooks│───▶│Notebooks│───▶│Notebooks│          │
│   │ 01-03   │    │ 04-06   │    │ 07-10   │          │
│   └─────────┘    └─────────┘    └─────────┘          │
│                                                        │
│   Dependencies:  #38 ──blocks──▶ #40 ──blocks──▶ #41  │
└────────────────────────────────────────────────────────┘
```

---

## Epic-Issue erstellen

### 1. Naming Convention

```
Title: "[EPIC] Kurze Beschreibung"
```

Das `[EPIC]` Prefix macht Epics in Listen sofort erkennbar.

### 2. Struktur der Description

```markdown
## Epic Overview

[2-3 Sätze Zusammenfassung]

## Goals

- Ziel 1
- Ziel 2
- Ziel 3

## Child Issues

| Issue | Beschreibung | Status | Weight |
|-------|--------------|--------|--------|
| #38 | Notebooks 01-03 | ✅ Done | 5 |
| #40 | Notebooks 04-06 | ✅ Done | 8 |
| #41 | Notebooks 07-10 | 🟡 In Progress | 13 |

## Dependencies

```
#38 ──blocks──▶ #40 ──blocks──▶ #41
```

## Timeline

| Milestone | Target | Status |
|-----------|--------|--------|
| v0.1 | 2026-02-01 | 🟡 In Progress |
| v0.2 | 2026-03-01 | 🔴 Not Started |

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### 3. Labels für Epics

```
type::feature          (oder type::documentation)
priority::high         (Epics sind meist wichtig)
component::*           (Hauptkomponente)
workflow::in-progress  (solange Child-Issues offen)
```

---

## Child-Issues verknüpfen

### In Child-Issue Description

```markdown
## Context

Part of [EPIC] #39 - CLARISSA Tutorial System

Relates to #39
```

### Automatische Verlinkung

GitLab erkennt `#39` automatisch und zeigt bidirektionale Links.

### Abhängigkeiten dokumentieren

```markdown
## Dependencies

- Depends on: #38 (muss zuerst fertig sein)
- Blocks: #41 (wartet auf dieses Issue)
```

---

## Epic-Workflow

### 1. Epic erstellen

```bash
# Via GitLab UI oder Template
Title: "[EPIC] Feature X Implementation"
Labels: type::feature, priority::high, workflow::backlog
```

### 2. Child-Issues erstellen

```bash
# Jedes Child-Issue referenziert das Epic
Description: "Part of Epic #39\n\nRelates to #39"
```

### 3. Fortschritt tracken

Die Child-Issue Tabelle im Epic manuell aktualisieren:

```markdown
| Issue | Status |
|-------|--------|
| #38 | ✅ Done |      # War: 🟡 In Progress
| #40 | ✅ Done |      # War: 🔴 Backlog
| #41 | 🟡 In Progress |
```

### 4. Epic schließen

Wenn alle Child-Issues geschlossen und Success Criteria erfüllt:

```bash
# Epic-Issue schließen
State: Closed
```

---

## Echtes Beispiel: Epic #39

### [EPIC] CLARISSA Interactive Tutorial System

**URL:** https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues/39

**Child-Issues:**

| Issue | Notebooks | MR | Status |
|-------|-----------|-----|--------|
| #38 | 01-03: ECLIPSE, OPM, Knowledge | !34 | ✅ Merged |
| #40 | 04-06: LLM, Constraints, Generator | !35 | ✅ Merged |
| #41 | 07-10: RL, RIGOR, Pipeline, API | !36 | ✅ Merged |

**Timeline:**
- Erstellt: 2026-01-18
- Child-Issues erstellt: 2026-01-18
- Alle MRs gemerged: 2026-01-18
- Epic abgeschlossen: (noch offen für weitere Arbeit)

**Was funktioniert hat:**
- Klare Child-Issue Struktur mit Abhängigkeiten
- Weight-basierte Aufwandsschätzung (5 + 8 + 13 = 26 Story Points)
- MR-Referenzen in Child-Issues
- Automatische Verlinkung durch `#39` Referenzen

---

## Issue Template

Nutze das Template `.gitlab/issue_templates/epic.md`:

```markdown
<!-- .gitlab/issue_templates/epic.md -->

## Epic Overview

[Beschreibe die Initiative in 2-3 Sätzen]

## Goals

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## Child Issues

| Issue | Beschreibung | Status | Weight |
|-------|--------------|--------|--------|
| #XX | Description | 🔴 Backlog | X |
| #YY | Description | 🔴 Backlog | Y |

## Dependencies

```
#XX ──blocks──▶ #YY
```

## Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Phase 1 | YYYY-MM-DD | 🔴 Not Started |
| Phase 2 | YYYY-MM-DD | 🔴 Not Started |

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2

---

/label ~"type::feature" ~"priority::high" ~"workflow::backlog"
```

---

## Best Practices

### ✅ DO

- `[EPIC]` Prefix im Titel
- Child-Issue Tabelle pflegen
- Abhängigkeiten dokumentieren
- Success Criteria definieren
- Epic schließen wenn fertig

### ❌ DON'T

- Epics für einzelne Tasks
- Child-Issues ohne Epic-Referenz
- Verwaiste Epics (nie aktualisiert)
- Zu viele Child-Issues (max ~10)

---

## Vergleich: GitLab Premium vs. Free Tier

| Feature | Premium Epics | Free Tier Pattern |
|---------|---------------|-------------------|
| Hierarchie | Automatisch | Manuell via Tabelle |
| Roadmap | ✅ Eingebaut | ❌ Nicht verfügbar |
| Burndown | ✅ Automatisch | ❌ Manuell |
| Child-Links | ✅ Native | 📝 Via `#XX` Referenz |
| Fortschritt | ✅ Berechnet | 📝 Manuell aktualisieren |

**Fazit:** Das Pattern funktioniert gut für kleine Teams. Bei >50 Issues pro Epic wird es unübersichtlich - dann lohnt sich Premium.

---

## Referenzen

- [Epic #39 (Live-Beispiel)](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues/39)
- [GitLab Premium Epics](https://docs.gitlab.com/ee/user/group/epics/)
- [project-management.md](project-management.md)
