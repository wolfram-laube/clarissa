# ADR-027: Bidirectional Sync Strategy

## Status

✅ **Accepted** - Implemented 2026-05-25

## Context

CLARISSA wird primär auf GitLab entwickelt (CI/CD, Runner-Infrastruktur, Issues), 
soll aber auch auf GitHub sichtbar sein für:
- Open Source Visibility
- Community Contributions
- Academic Citations

## Decision

**GitLab als Primary, GitHub als Mirror mit bidirektionalem Sync:**

```
┌─────────────┐         ┌─────────────┐
│   GitLab    │ ──────► │   GitHub    │
│  (Primary)  │ auto    │  (Mirror)   │
│             │ push    │             │
│  CI/CD      │         │  Visibility │
│  Runners    │ ◄────── │  PRs        │
│  Issues     │ manual  │  Community  │
└─────────────┘ pull    └─────────────┘
```

### Sync-Jobs

| Job | Trigger | Richtung |
|-----|---------|----------|
| `github-push` | auto (main) | GitLab → GitHub |
| `github-pull` | manual | GitHub → GitLab |
| `github-status` | manual | Status Check |

### Konflikt-Strategie

- **GitLab wins**: Bei Konflikten ist GitLab die Source of Truth
- `--force-with-lease`: Sicheres Force-Push mit Schutz vor Race Conditions
- Externe PRs auf GitHub werden manuell nach GitLab gezogen

## Alternatives Considered

1. **GitLab Push Mirror (Settings)**
   - Pro: Einfach, automatisch
   - Con: Nur unidirektional, keine Kontrolle

2. **GitHub Actions → GitLab**
   - Pro: Bidirektional
   - Con: Doppelte CI-Infrastruktur

3. **Externes Tool (git-sync, repo-sync)**
   - Pro: Feature-reich
   - Con: Zusätzliche Dependency

## Consequences

### Positive
- Volle Kontrolle über Sync-Zeitpunkt und -Richtung
- Nutzt bestehende Runner-Infrastruktur
- Auditierbar in CI/CD Logs
- Flexibel erweiterbar

### Negative
- Manueller Schritt für GitHub→GitLab
- GITHUB_TOKEN muss gepflegt werden

## Implementation

- Pipeline: `.gitlab/github-sync.yml`
- Issue: #157
- Variable: `GITHUB_TOKEN` (Gruppen-Ebene, masked)

---
*Last updated: 2026-05-25*
