# 🦊 CLARISSA GitLab Workflow Cheatsheet

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue closed automatically

---

## 🔄 The Workflow in 5 Steps

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Pick    │───▶│  2. Create  │───▶│  3. Commit  │───▶│  4. Create  │───▶│  5. Review  │
│    Issue    │    │   Branch    │    │   & Push    │    │     MR      │    │   & Merge   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 1️⃣ Pick Issue from Board

```
Project → Plan → Issue Boards
```

- Take an issue from the **Ready** column
- Move it to **In Progress**

---

## 2️⃣ Create Branch

```bash
# ALWAYS start with issue number!
git checkout -b 42-short-description
```

| ✅ Good | ❌ Bad |
|---------|--------|
| `42-add-login` | `my-branch` |
| `12-fix-bug` | `test123` |
| `7-update-docs` | `changes` |

---

## 3️⃣ Commits with Issue Reference

```bash
git commit -m "type: description #42"
```

### Conventional Commits Prefixes:

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `chore:` | Maintenance |
| `refactor:` | Code restructuring |
| `test:` | Tests |

### Examples:

```bash
git commit -m "feat: add user authentication #42"
git commit -m "fix: resolve null pointer exception #15"
git commit -m "docs: update installation guide #7"
```

---

## 4️⃣ Create Merge Request

```bash
git push -u origin 42-short-description
```

### MR Description Template:

```markdown
## Summary
Brief description of changes.

## Changes
- Item 1
- Item 2

## Related
Closes #42

## Checklist
- [ ] Code tested
- [ ] Documentation updated
```

**Important:** `Closes #42` automatically closes the issue on merge!

---

## 5️⃣ Review & Merge

1. Reviewer examines code
2. On approval: Click **Merge**
3. ✅ Issue is automatically closed!

---

## 🔗 Magic Keywords

These words in commit or MR automatically close issues:

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Closes issue on merge |
| `Fixes #42` | Closes issue on merge |
| `Resolves #42` | Closes issue on merge |
| `#42` | Link only |

---

## 🚫 The Cardinal Sins

1. ❌ Pushing directly to `main`
2. ❌ Commits without issue reference (`#42`)
3. ❌ Committing secrets/passwords
4. ❌ Huge MRs with 50 files
5. ❌ MR without `Closes #X`

---

## ✅ Pre-Merge Checklist

- [ ] Branch name includes issue number
- [ ] Commits follow Conventional Commits
- [ ] Commits reference issue (`#42`)
- [ ] MR includes `Closes #42`
- [ ] CI pipeline is green
- [ ] Issue label set to `workflow::review`

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Issue Board | `/-/boards` |
| All Issues | `/-/issues` |
| Merge Requests | `/-/merge_requests` |
| Interactive Slides | `docs/guides/contributing/workflow-slides.html` |

---

*Questions? Create an issue with label `help-wanted`*
