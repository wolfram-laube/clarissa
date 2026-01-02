# 🦊 CLARISSA GitLab Workflow - Kurzreferenz

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue schließt automatisch

---

## 🔄 Der Workflow in 5 Schritten

## 1️⃣ Issue vom Board wählen

```
Project → Plan → Issue Boards
```

- Nimm Issue aus **Ready**-Spalte
- Verschiebe nach **In Progress**

## 2️⃣ Branch erstellen

```bash
git checkout -b 42-short-description
```

## 3️⃣ Commit mit Issue-Referenz

```bash
git commit -m "type: description #42"
```

| Prefix | Usage |
|--------|-------|
| `feat:` | Neues Feature |
| `fix:` | Fehlerbehebung |
| `docs:` | Dokumentation |
| `chore:` | Wartung |
| `refactor:` | Code-Refactoring |
| `test:` | Tests |

## 4️⃣ Merge Request erstellen

```bash
git push -u origin 42-short-description
```

**Closes #42 schließt Issue automatisch beim Merge!**

## 5️⃣ Review & Merge

1. Reviewer prüft Code
2. Nach Genehmigung: Klicke **Merge**
3. Issue schließt automatisch!

---

## 🔗 Zauberwörter

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Auto-close on merge |
| `Fixes #42` | Auto-close on merge |
| `#42` | Link only |

---

## 🚫 Verboten


---

## ✅ Checkliste vor dem Merge


---

*Hast du eine Frage? Erstelle ein Issue mit dem Label help-wanted*