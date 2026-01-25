# Epics in GitLab Free Tier

Since GitLab Free doesn't support native Epics, we use **Issues as Epics** with a structured pattern.

> 💡 **Example:** [Epic #39 - CLARISSA Tutorial System](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/39)

---

## Why Epics?

Epics group related issues into a larger initiative:

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

## Creating an Epic Issue

### 1. Naming Convention

```
Title: "[EPIC] Short Description"
```

The `[EPIC]` prefix makes Epics immediately recognizable in lists.

### 2. Description Structure

```markdown
## Epic Overview

[2-3 sentence summary]

## Goals

- Goal 1
- Goal 2
- Goal 3

## Child Issues

| Issue | Description | Status | Weight |
|-------|-------------|--------|--------|
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

### 3. Labels for Epics

```
type::epic             (dedicated epic label)
priority::high         (Epics are usually important)
component::*           (main component)
workflow::in-progress  (while child issues are open)
```

---

## Linking Child Issues

### In Child Issue Description

```markdown
## Context

Part of [EPIC] #39 - CLARISSA Tutorial System

Relates to #39
```

### Automatic Linking

GitLab automatically recognizes `#39` and shows bidirectional links.

### Documenting Dependencies

```markdown
## Dependencies

- Depends on: #38 (must be completed first)
- Blocks: #41 (waiting on this issue)
```

---

## Epic Workflow

### 1. Create Epic

```bash
# Via GitLab UI or template
Title: "[EPIC] Feature X Implementation"
Labels: type::epic, priority::high, workflow::backlog
```

### 2. Create Child Issues

```bash
# Each child issue references the epic
Description: "Part of Epic #39

Relates to #39"
```

### 3. Track Progress

Manually update the child issue table in the epic:

```markdown
| Issue | Status |
|-------|--------|
| #38 | ✅ Done |      # Was: 🟡 In Progress
| #40 | ✅ Done |      # Was: 🔴 Backlog
| #41 | 🟡 In Progress |
```

### 4. Close Epic

When all child issues are closed and success criteria met:

```bash
# Close epic issue
State: Closed
```

---

## Real Example: Epic #39

### [EPIC] CLARISSA Interactive Tutorial System

**URL:** https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/39

**Child Issues:**

| Issue | Notebooks | MR | Status |
|-------|-----------|-----|--------|
| #38 | 01-03: ECLIPSE, OPM, Knowledge | !34 | ✅ Merged |
| #40 | 04-06: LLM, Constraints, Generator | !35 | ✅ Merged |
| #41 | 07-10: RL, RIGOR, Pipeline, API | !36 | ✅ Merged |

**Timeline:**
- Created: 2026-01-18
- Child issues created: 2026-01-18
- All MRs merged: 2026-01-18
- Epic closed: (still open for further work)

**What worked well:**
- Clear child issue structure with dependencies
- Weight-based effort estimation (5 + 8 + 13 = 26 story points)
- MR references in child issues
- Automatic linking through `#39` references

---

## Issue Template

Use the template `.gitlab/issue_templates/epic.md`:

```markdown
<!-- .gitlab/issue_templates/epic.md -->

## Epic Overview

[Describe the initiative in 2-3 sentences]

## Goals

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## Child Issues

| Issue | Description | Status | Weight |
|-------|-------------|--------|--------|
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

/label ~"type::epic" ~"priority::high" ~"workflow::backlog"
```

---

## Best Practices

### ✅ DO

- `[EPIC]` prefix in title
- Maintain child issue table
- Document dependencies
- Define success criteria
- Close epic when complete

### ❌ DON'T

- Epics for single tasks
- Child issues without epic reference
- Orphaned epics (never updated)
- Too many child issues (max ~10)

---

## Comparison: GitLab Premium vs. Free Tier

| Feature | Premium Epics | Free Tier Pattern |
|---------|---------------|-------------------|
| Hierarchy | Automatic | Manual via table |
| Roadmap | ✅ Built-in | ❌ Not available |
| Burndown | ✅ Automatic | ❌ Manual |
| Child links | ✅ Native | 📝 Via `#XX` reference |
| Progress | ✅ Calculated | 📝 Manual update |

**Conclusion:** The pattern works well for small teams. With >50 issues per epic, it becomes unwieldy - then Premium is worth it.

---

## References

- [Epic #39 (Live Example)](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/issues/39)
- [GitLab Premium Epics](https://docs.gitlab.com/ee/user/group/epics/)
- [project-management.md](project-management.md)
