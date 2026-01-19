# Project Management Guide

This document describes the complete project management setup for CLARISSA in GitLab.

> 🏗️ **Architecture Decision:** [ADR-018](../architecture/adr/ADR-018-gitlab-pm-workflow.md)  
> 📖 **Workflow:** [CONTRIBUTING.md](../contributing.md)

---

## Overview

CLARISSA uses GitLab as **Single Source of Truth** for:

| Area | GitLab Feature |
|------|----------------|
| Issue Tracking | Issues |
| Larger Initiatives | Epics (via Issue Links) |
| Sprint Planning | Milestones |
| Task Visualization | Issue Board |
| Code Review | Merge Requests |
| Automation | CI/CD Pipelines |
| Documentation | Repository + GitLab Pages |

---

## Label Taxonomy

### Scoped Labels

GitLab **Scoped Labels** (`scope::value`) ensure only one label per scope is active:

```
type::feature + type::bug  → Not allowed ✗
type::feature              → OK ✓
```

### Complete Label Reference

#### `type::` - Type of Work

| Label | Hex Color | Description |
|-------|-----------|-------------|
| `type::feature` | `#428BCA` | New functionality |
| `type::bug` | `#D73A4A` | Bug fix |
| `type::docs` | `#CCCCCC` | Documentation |
| `type::chore` | `#795548` | Maintenance |
| `type::research` | `#9C27B0` | Spikes, investigations |
| `type::adr` | `#00BCD4` | Architecture Decision Record |
| `type::task` | `#1E88E5` | General tasks |
| `type::fix` | `#FB8C00` | Small fixes |
| `type::epic` | `#6699CC` | Epic (parent issue) |

#### `priority::` - Urgency

| Label | Hex Color | SLA |
|-------|-----------|-----|
| `priority::critical` | `#B71C1C` | Immediate (< 24h) |
| `priority::high` | `#E65100` | This week |
| `priority::medium` | `#FDD835` | This sprint (2 weeks) |
| `priority::low` | `#64B5F6` | Backlog |

#### `component::` - System Area

| Label | Architecture Component |
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
| `component::paper` | Scientific Publications |
| `component::ci` | GitLab CI/CD Pipeline |

#### `workflow::` - Work Status

| Label | Board Column | Trigger |
|-------|--------------|---------|
| `workflow::backlog` | Backlog | Issue created |
| `workflow::ready` | Ready | Sprint planning |
| `workflow::in-progress` | In Progress | Work begins |
| `workflow::review` | Review | MR created |
| `workflow::blocked` | Blocked | Dependency missing |
| `workflow::done` | Done | Merged/Closed |

#### Special Labels (non-scoped)

| Label | Usage |
|-------|-------|
| `good-first-issue` | Beginner-friendly, well documented |
| `help-wanted` | External help welcome |
| `needs-discussion` | Team decision required |
| `wontfix` | Intentionally not implemented |
| `duplicate` | Reference to original issue |

---

## Milestones

### Release Structure

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

### Milestone Details

| Milestone | Focus | Key Results |
|-----------|-------|-------------|
| **v0.1 - Foundation** | Groundwork | CI/CD ✅, Architecture ✅, Runner Matrix ✅ |
| **v0.2 - SPE Europe Draft** | Conference | Paper Draft, OPM Integration, Tutorials |
| **v0.3 - NLP Pipeline** | Conversation | Intent Classification, Entity Extraction |
| **v0.4 - ECLIPSE Parser** | Deck Handling | Parser, Validator, Generator |
| **v1.0 - Production** | Release | Full Integration, Testing, Docs |

### Milestone Usage

1. **Create issue** → Assign milestone
2. **Burndown** automatically in GitLab
3. **Close milestone** when all issues done

---

## Issue Board

### Board Configuration

The [CLARISSA Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) has the following lists:

| List | Scope | Filter |
|------|-------|--------|
| **Open** | All | No `workflow::` label |
| **Backlog** | Planned | `workflow::backlog` |
| **Ready** | Sprint | `workflow::ready` |
| **In Progress** | Active | `workflow::in-progress` |
| **Review** | MR open | `workflow::review` |
| **Blocked** | Waiting | `workflow::blocked` |

### Board Workflow

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

- Issue from **Backlog** → **Ready** = Sprint planning
- Issue from **Ready** → **In Progress** = Work begins
- Label is automatically updated!

---

## Epics

Since GitLab Free doesn't have native Epics, we use **Issues as Epics**:

### Create an Epic Issue

```markdown
Title: "[EPIC] Interactive Tutorial Series"
Labels: type::epic, priority::high

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

### Link Child Issues

In each child issue:
```markdown
Relates to #39
Part of Epic #39
```

---

## Issue Templates

Available templates in `.gitlab/issue_templates/`:

| Template | Usage |
|----------|-------|
| `adr.md` | Architecture Decision Record |
| `bug.md` | Bug Report |
| `feature.md` | Feature Request |

### Using a Template

1. New Issue → Choose a template
2. Fill in fields
3. Set labels/milestone
4. Submit

---

## Metrics

### Velocity Tracking

- **Issues closed per milestone** = Velocity
- **Burndown chart** in milestone view
- **Time tracking** via `/spend 2h` commands

### Label Statistics

```
GitLab → Issues → Labels → Click on label → Issue count
```

---

## CI/CD Integration

### Auto-Close via MR

```yaml
# .gitlab-ci.yml is already configured
# MR merge → Issue auto-close when:
# - "Closes #X" in commit
# - "Fixes #X" in MR description
```

### Pipeline Status in Board

- 🟢 Pipeline green → MR can be merged
- 🔴 Pipeline red → Fix required

---

## References

- [GitLab Issue Management](https://docs.gitlab.com/ee/user/project/issues/)
- [GitLab Boards](https://docs.gitlab.com/ee/user/project/issue_board.html)
- [Scoped Labels](https://docs.gitlab.com/ee/user/project/labels.html#scoped-labels)
- [ADR-018](../architecture/adr/ADR-018-gitlab-pm-workflow.md)

---

*Created as part of Issue #43*
