# CLARISSA Project Management Guide

This document describes the project management setup for CLARISSA using GitLab's built-in features.

## Overview

CLARISSA uses GitLab's native issue tracking as a JIRA alternative, providing tight integration between issues, merge requests, and code.

## Issue ↔ Code Integration

### Linking Methods

| Method | Syntax | Effect |
|--------|--------|--------|
| **Commit Message** | `fix: resolve auth bug #42` | Creates link to issue |
| **Auto-Close** | `Closes #42` or `Fixes #42` | Closes issue on merge |
| **MR Description** | `Implements #42` | Bidirectional link |
| **Branch Name** | `42-feature-name` | Auto-detected by GitLab |
| **Create MR from Issue** | "Create merge request" button | Creates branch + MR |

### Recommended Workflow

```bash
# 1. Start work on issue #42
git checkout -b 42-implement-adapter

# 2. Make commits referencing the issue
git commit -m "feat(simulators): add OPM adapter base class #42"

# 3. Create MR with closing keyword
# MR description: "Implements #42\n\nCloses #42"

# 4. On merge, issue #42 automatically closes
```

## Label System

### Scoped Labels (Mutually Exclusive)

GitLab scoped labels (using `::`) ensure only one label per scope can be applied:

#### Type (`type::`)
| Label | Color | Use For |
|-------|-------|---------|
| `type::feature` | 🟢 Green | New functionality |
| `type::bug` | 🔴 Red | Defects |
| `type::task` | 🔵 Blue | General work |
| `type::docs` | ⚪ Gray | Documentation |
| `type::research` | 🟣 Purple | Spikes, investigations |
| `type::adr` | 🔵 Cyan | Architecture decisions |

#### Priority (`priority::`)
| Label | Color | Meaning |
|-------|-------|---------|
| `priority::critical` | 🔴 | Drop everything |
| `priority::high` | 🟠 | Address this sprint |
| `priority::medium` | 🟡 | Normal priority |
| `priority::low` | 🔵 | When time permits |

#### Component (`component::`)
| Label | Description |
|-------|-------------|
| `component::nlp-agent` | NLP/Conversational interface |
| `component::simulators` | OPM, ECLIPSE adapters |
| `component::governance` | Validation layer |
| `component::learning` | Feedback systems |
| `component::infrastructure` | CI/CD, Docker, K8s |
| `component::docs` | Documentation |
| `component::data-mesh` | Data storage layer |

#### Workflow (`workflow::`)
| Label | Board Column |
|-------|--------------|
| `workflow::backlog` | Not yet planned |
| `workflow::ready` | Ready to start |
| `workflow::in-progress` | Being worked on |
| `workflow::review` | MR open |
| `workflow::blocked` | Waiting on dependency |

### Special Labels
- `good-first-issue` - Newcomer-friendly
- `help-wanted` - Needs attention
- `needs-discussion` - Requires team input

## Milestones

Milestones represent releases/versions:

| Milestone | Focus |
|-----------|-------|
| v0.1.0 - Foundation | Architecture, CI/CD baseline |
| v0.2.0 - OPM Flow Integration | OPM simulator integration |
| v0.3.0 - NLP Pipeline MVP | Basic NLP capabilities |
| v0.4.0 - ECLIPSE Parser | ECLIPSE deck parsing |
| v1.0.0 - Production Ready | First release |

## Issue Board Setup

GitLab Free tier allows one board. Configure it with workflow labels:

**Board Lists:**
1. Open (no workflow label)
2. `workflow::ready`
3. `workflow::in-progress`
4. `workflow::review`
5. `workflow::blocked`
6. Closed

To create: **Project → Plan → Issue Boards → Edit board**

## Issue Templates

Templates available when creating new issues:
- **Feature** - New functionality
- **Bug** - Defect report
- **Task** - General work
- **ADR** - Architecture decisions

## Weight (Story Points)

Use the Weight field for estimation:
- **1** - Trivial (< 1 hour)
- **2** - Small (< 4 hours)
- **3** - Medium (1 day)
- **5** - Large (2-3 days)
- **8** - Extra Large (1 week)
- **13** - Epic-sized (break it down!)

## Quick Reference

### Creating Issues from CLI
```bash
# Using glab CLI (optional)
glab issue create --title "Fix bug" --label "type::bug,priority::high"
```

### Commit Message Format
```
<type>(<scope>): <description> #<issue>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`

### Closing Keywords
These keywords in MR descriptions auto-close issues:
- `Closes #N`
- `Fixes #N`
- `Resolves #N`

## Best Practices

1. **One issue per feature/bug** - Keep scope focused
2. **Link everything** - Reference issues in commits and MRs
3. **Update workflow labels** - Move issues through the board
4. **Use weights** - Enable velocity tracking
5. **Milestone assignment** - Plan releases effectively
