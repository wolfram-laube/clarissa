# CLARISSA Workflow Cheatsheet

> 📋 Quick reference for daily development. Full guide: [CONTRIBUTING.md](../../contributing.md)

---

## 🔄 Workflow in 30 Sekunden

```bash
# 1. Issue existiert: #43

# 2. Branch erstellen
git checkout main && git pull
git checkout -b feature/43-my-feature

# 3. Entwickeln & committen
git add .
git commit -m "feat(scope): description"

# 4. Letzter Commit mit Auto-Close
git commit -m "feat: final changes

Closes #43"

# 5. Push & MR erstellen
git push -u origin feature/43-my-feature
# → MR via GitLab UI erstellen
```

---

## 🏷️ Labels Quick Reference

### Type (`type::`)
| Label | Use |
|-------|-----|
| `type::feature` | Neues Feature |
| `type::bug` | Bugfix |
| `type::documentation` | Docs |
| `type::chore` | Maintenance |

### Priority (`priority::`)
| Label | Urgency |
|-------|---------|
| `priority::critical` | 🔴 Sofort |
| `priority::high` | 🟠 Diese Woche |
| `priority::medium` | 🟡 Dieser Sprint |
| `priority::low` | 🔵 Wenn Zeit |

### Workflow (`workflow::`)
| Label | Status |
|-------|--------|
| `workflow::backlog` | Noch nicht begonnen |
| `workflow::ready` | Bereit |
| `workflow::in-progress` | In Arbeit |
| `workflow::review` | MR offen |
| `workflow::blocked` | Blockiert |

---

## 📝 Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer: Closes #X]
```

### Types
| Type | Use |
|------|-----|
| `feat` | Neues Feature |
| `fix` | Bugfix |
| `docs` | Dokumentation |
| `chore` | Maintenance |
| `refactor` | Refactoring |
| `test` | Tests |
| `ci` | CI/CD |

### Examples
```bash
feat(tutorials): add notebook 07
fix(ci): correct docker tag
docs: update README
chore: bump dependencies
```

---

## 🌿 Branch Naming

```
<type>/<issue-id>-<short-description>
```

| Type | Example |
|------|---------|
| Feature | `feature/43-pm-docs` |
| Bugfix | `fix/44-parser-crash` |
| Docs | `docs/45-api-guide` |
| Chore | `chore/46-deps-update` |

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Board | [gitlab.com/.../boards](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) |
| Issues | [gitlab.com/.../issues](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues) |
| MRs | [gitlab.com/.../merge_requests](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/merge_requests) |
| Pipelines | [gitlab.com/.../pipelines](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines) |

---

## ⚡ Pro Tips

1. **Pipeline rot?** → Fixen, neu pushen, warten
2. **MR-Title** = Hauptcommit-Message
3. **`Closes #X`** im letzten Commit = Auto-Close
4. **Kleine MRs** < 500 Zeilen = schnelleres Review
5. **Labels setzen** beim Issue-Erstellen

---

*Version 1.0 | [Full Guide](../../contributing.md)*
