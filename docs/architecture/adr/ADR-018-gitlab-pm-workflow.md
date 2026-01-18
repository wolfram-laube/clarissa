# ADR-018: GitLab-Native Project Management Workflow

**Status:** Accepted  
**Date:** 2026-01-03 (originally), 2026-01-18 (renumbered)  
**Decision Makers:** Wolfram Laube  
**Tags:** workflow, project-management, gitlab

> **Note:** This ADR was originally numbered ADR-001 in a separate `decisions/` directory.
> Renumbered to ADR-018 during consolidation (see Issue #52).

## Context

CLARISSA requires a structured development workflow that:

- Ensures traceable changes
- Guarantees code quality through reviews
- Enforces automated tests before merge
- Keeps documentation and code in sync
- Remains practical for a small team (1-3 people)

### Alternatives Considered

1. **GitHub Flow** - Simple branch-per-feature, PR-based
2. **GitFlow** - Complex branch structure (develop, release, hotfix)
3. **Trunk-Based Development** - Short feature branches, frequent merges
4. **GitLab Flow** - Environment branches + feature branches

## Decision

We use a **GitLab-native workflow** with the following hierarchy:

```
Epic (cross-milestone)
  └── Issue (single task)
        └── Feature Branch (feature/{issue-id}-{slug})
              └── Merge Request (→ main)
```

### Core Principles

1. **No direct push to `main`** - All changes via MR
2. **Issue-First** - Every work item starts with an issue
3. **Branch Naming** - `feature/{issue-id}-{short-description}`
4. **Conventional Commits** - `feat:`, `fix:`, `docs:`, `chore:`
5. **Auto-Close** - MR commit contains `Closes #{issue-id}`
6. **Pipeline Gate** - Merge only after successful CI

### When to Create an Epic?

Since GitLab Free doesn't offer native Epics, we use parent issues with `[EPIC]` prefix and `type::epic` label.

| Situation | Epic? | Rationale |
|-----------|-------|-----------|
| 3+ related issues | ✅ Yes | Grouping is beneficial |
| Cross-milestone work | ✅ Yes | Tracking across milestones |
| Isolated fixes (1-2 issues) | ❌ No | Overhead without benefit |
| Effort < 1 day | ❌ No | Too small for Epic |

**Epic Format:**
```markdown
## [EPIC] Feature Name

Labels: type::epic, priority::X, workflow::in-progress

### Child Issues
- [ ] #XX - Subtask 1
- [ ] #XX - Subtask 2
```

### Workflow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Issue     │────▶│   Create    │────▶│   Commits   │────▶│     MR      │
│   Board     │     │   Branch    │     │   + Push    │     │   + Review  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
       ┌───────────────────────────────────────────────────────────┘
       ▼
┌─────────────┐     ┌─────────────┐
│   CI/CD     │────▶│   Merge     │
│   Pipeline  │     │   + Close   │
└─────────────┘     └─────────────┘
```

## Consequences

### Positive

- **Traceability**: Every code change is traceable to an issue
- **Automation**: `Closes #X` automatically closes issues
- **Quality Gate**: CI pipeline prevents broken code on main
- **Documentation**: Issues and MRs form natural project history
- **Single Source of Truth**: Everything in GitLab, no external tools needed

### Negative

- **Overhead for small changes**: Even typo fixes require issue + MR
- **Learning curve**: Team must internalize the workflow
- **CI dependency**: Blocked when CI has problems

### Risks

- **Review bottleneck**: Mitigated by small, focused MRs
- **Stale branches**: Mitigated by `remove_source_branch: true`

## Implementation

See [Contributing Guide](../../contributing.md) for the detailed workflow.

## References

- [GitLab Flow Documentation](https://docs.gitlab.com/ee/topics/gitlab_flow.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- Issue #52: ADR Directory Consolidation
