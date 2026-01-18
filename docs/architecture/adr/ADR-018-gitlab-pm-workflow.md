# ADR-018: GitLab-Native Project Management Workflow

**Status:** Accepted  
**Date:** 2026-01-03 (originally), 2026-01-18 (renumbered)  
**Decision Makers:** Wolfram Laube  
**Tags:** workflow, project-management, gitlab

> **Note:** This ADR was originally numbered ADR-001 in a separate `decisions/` directory.
> Renumbered to ADR-018 during consolidation (see Issue #52).

## Context

CLARISSA benötigt einen strukturierten Entwicklungsworkflow, der:
- Nachvollziehbare Änderungen gewährleistet
- Code-Qualität durch Reviews sicherstellt
- Automatisierte Tests vor dem Merge erzwingt
- Dokumentation und Code synchron hält
- Für ein kleines Team (1-3 Personen) praktikabel ist

### Betrachtete Alternativen

1. **GitHub Flow** - Simple branch-per-feature, PR-basiert
2. **GitFlow** - Komplexe Branch-Struktur (develop, release, hotfix)
3. **Trunk-Based Development** - Kurze Feature-Branches, häufige Merges
4. **GitLab Flow** - Environment-Branches + Feature-Branches

## Decision

Wir verwenden einen **GitLab-nativen Workflow** mit folgender Hierarchie:

```
Epic (Milestone-übergreifend)
  └── Issue (einzelne Aufgabe)
        └── Feature-Branch (feature/{issue-id}-{slug})
              └── Merge Request (→ main)
```

### Kernprinzipien

1. **Kein direkter Push auf `main`** - Alle Änderungen via MR
2. **Issue-First** - Jede Arbeit beginnt mit einem Issue
3. **Branch-Naming** - `feature/{issue-id}-{kurzbeschreibung}`
4. **Conventional Commits** - `feat:`, `fix:`, `docs:`, `chore:`
5. **Auto-Close** - MR-Commit enthält `Closes #{issue-id}`
6. **Pipeline-Gate** - Merge nur nach erfolgreicher CI

### Wann Epic erstellen?

Da GitLab Free keine nativen Epics bietet, nutzen wir Parent-Issues mit `[EPIC]` Prefix und `type::epic` Label.

| Situation | Epic? | Begründung |
|-----------|-------|------------|
| 3+ zusammenhängende Issues | ✅ Ja | Gruppierung sinnvoll |
| Milestone-übergreifende Arbeit | ✅ Ja | Tracking über Milestones hinweg |
| Isolierte Fixes (1-2 Issues) | ❌ Nein | Overhead ohne Mehrwert |
| Zeitaufwand < 1 Tag | ❌ Nein | Zu klein für Epic |

**Epic-Format:**
```markdown
## [EPIC] Feature Name

Labels: type::epic, priority::X, workflow::in-progress

### Child Issues
- [ ] #XX - Subtask 1
- [ ] #XX - Subtask 2
```

### Workflow-Diagramm

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Issue     │────▶│   Branch    │────▶│   Commits   │────▶│     MR      │
│   Board     │     │   erstellen │     │   + Push    │     │   + Review  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
       ┌───────────────────────────────────────────────────────────┘
       ▼
┌─────────────┐     ┌─────────────┐
│  CI/CD      │────▶│   Merge     │
│  Pipeline   │     │   + Close   │
└─────────────┘     └─────────────┘
```

## Consequences

### Positive

- **Traceability**: Jede Codeänderung ist zu einem Issue zurückverfolgbar
- **Automatisierung**: `Closes #X` schließt Issues automatisch
- **Quality Gate**: CI-Pipeline verhindert kaputten Code auf main
- **Dokumentation**: Issues und MRs bilden natürliche Projekthistorie
- **Single Source of Truth**: Alles in GitLab, keine externen Tools nötig

### Negative

- **Overhead für Kleinigkeiten**: Auch Typo-Fixes brauchen Issue + MR
- **Lernkurve**: Team muss Workflow verinnerlichen
- **CI-Abhängigkeit**: Blockiert bei CI-Problemen

### Risiken

- **Bottleneck bei Reviews**: Mitigiert durch kleine, fokussierte MRs
- **Stale Branches**: Mitigiert durch `remove_source_branch: true`

## Implementation

Siehe [Contributing Guide](../../contributing.md) für den detaillierten Workflow.

## References

- [GitLab Flow Documentation](https://docs.gitlab.com/ee/topics/gitlab_flow.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- Issue #52: ADR Directory Consolidation
