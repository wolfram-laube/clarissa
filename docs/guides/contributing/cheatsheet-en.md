# 🦊 CLARISSA GitLab Workflow - Quick Reference

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue auto-closes

---

## 🔄 The Workflow in 5 Steps

## 1️⃣ Pick Issue from Board

```
Project → Plan → Issue Boards
```

- Take issue from **Ready** column
- Move to **In Progress**

## 2️⃣ Create Branch

```bash
git checkout -b 42-short-description
```

## 3️⃣ Commit with Issue Reference

```bash
git commit -m "type: description #42"
```

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `chore:` | Maintenance |
| `refactor:` | Code refactoring |
| `test:` | Tests |

## 4️⃣ Create Merge Request

```bash
git push -u origin 42-short-description
```

**Closes #42 auto-closes issue on merge!**

## 5️⃣ Review & Merge

1. Reviewer checks code
2. When approved: Click **Merge**
3. Issue closes automatically!

---

## 🔗 Magic Words

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Auto-close on merge |
| `Fixes #42` | Auto-close on merge |
| `#42` | Link only |

---

## 🚫 Don'ts


---

## ✅ Pre-Merge Checklist


---

*Have a question? Create an issue with the help-wanted label*