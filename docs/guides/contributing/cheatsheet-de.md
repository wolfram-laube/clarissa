# 🦊 CLARISSA GitLab Workflow Cheatsheet

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue closed automatically

---

## 🔄 Der Workflow in 5 Schritten

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Issue   │───▶│  2. Branch  │───▶│  3. Commit  │───▶│   4. MR     │───▶│  5. Merge   │
│   wählen    │    │  erstellen  │    │   pushen    │    │  erstellen  │    │   & Done    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 1️⃣ Issue aus Board wählen

```
Project → Plan → Issue Boards
```

- Nimm ein Issue aus der **Ready**-Spalte
- Ziehe es nach **In Progress**

---

## 2️⃣ Branch erstellen

```bash
# IMMER mit Issue-Nummer beginnen!
git checkout -b 42-kurze-beschreibung
```

| ✅ Gut | ❌ Schlecht |
|--------|-------------|
| `42-add-login` | `my-branch` |
| `12-fix-bug` | `test123` |
| `7-update-docs` | `changes` |

---

## 3️⃣ Commits mit Issue-Referenz

```bash
git commit -m "typ: beschreibung #42"
```

### Conventional Commits Prefixes:

| Prefix | Verwendung |
|--------|------------|
| `feat:` | Neue Funktion |
| `fix:` | Bugfix |
| `docs:` | Dokumentation |
| `chore:` | Maintenance |
| `refactor:` | Code-Umbau |
| `test:` | Tests |

### Beispiele:

```bash
git commit -m "feat: add user authentication #42"
git commit -m "fix: resolve null pointer exception #15"
git commit -m "docs: update installation guide #7"
```

---

## 4️⃣ Merge Request erstellen

```bash
git push -u origin 42-kurze-beschreibung
```

### MR-Beschreibung Template:

```markdown
## Summary
Kurze Beschreibung der Änderungen.

## Changes
- Punkt 1
- Punkt 2

## Related
Closes #42

## Checklist
- [ ] Code getestet
- [ ] Dokumentation aktualisiert
```

**Wichtig:** `Closes #42` schließt das Issue automatisch beim Merge!

---

## 5️⃣ Review & Merge

1. Reviewer prüft Code
2. Bei Approval: **Merge** klicken
3. ✅ Issue wird automatisch geschlossen!

---

## 🔗 Magische Keywords

Diese Wörter in Commit oder MR schließen Issues automatisch:

| Keyword | Effekt |
|---------|--------|
| `Closes #42` | Schließt Issue bei Merge |
| `Fixes #42` | Schließt Issue bei Merge |
| `Resolves #42` | Schließt Issue bei Merge |
| `#42` | Nur verlinken |

---

## 🚫 Die Todsünden

1. ❌ Direkt auf `main` pushen
2. ❌ Commits ohne Issue-Referenz (`#42`)
3. ❌ Secrets/Passwörter committen
4. ❌ Riesige MRs mit 50 Dateien
5. ❌ MR ohne `Closes #X`

---

## ✅ Checkliste vor Merge

- [ ] Branch-Name enthält Issue-Nummer
- [ ] Commits folgen Conventional Commits
- [ ] Commits referenzieren Issue (`#42`)
- [ ] MR enthält `Closes #42`
- [ ] CI-Pipeline ist grün
- [ ] Issue-Label auf `workflow::review`

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Issue Board | `/-/boards` |
| Alle Issues | `/-/issues` |
| Merge Requests | `/-/merge_requests` |
| Diese Slides | `docs/guides/gitlab-workflow-slides.html` |

---

*Fragen? Issue erstellen mit Label `help-wanted`*
