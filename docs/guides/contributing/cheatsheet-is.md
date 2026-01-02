# 🦊 CLARISSA GitLab Workflow - Þjöppuð leiðbeining

> **TL;DR:** Issue → Grein → Commit → MR → Sameina → Issue lokast sjálfkrafa

---

## 🔄 Verkflæðið í 5 skrefum

## 1️⃣ Veldu Issue af borðinu

```
Project → Plan → Issue Boards
```

- Taktu issue úr **Ready** dálkinum
- Færðu í **In Progress**

## 2️⃣ Búðu til grein

```bash
git checkout -b 42-short-description
```

## 3️⃣ Commit með issue-tilvísun

```bash
git commit -m "type: description #42"
```

| Prefix | Usage |
|--------|-------|
| `feat:` | Nýr eiginleiki |
| `fix:` | Villuleiðrétting |
| `docs:` | Skjölun |
| `chore:` | Viðhald |
| `refactor:` | Endurskipulagning kóða |
| `test:` | Prófanir |

## 4️⃣ Búðu til Merge Request

```bash
git push -u origin 42-short-description
```

**Closes #42 lokar issue sjálfkrafa við sameiningu!**

## 5️⃣ Rýni & sameining

1. Rýnir skoðar kóða
2. Þegar samþykkt: Smelltu á **Merge**
3. Issue lokast sjálfkrafa!

---

## 🔗 Töfraorðin

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Auto-close on merge |
| `Fixes #42` | Auto-close on merge |
| `#42` | Link only |

---

## 🚫 Bannað


---

## ✅ Gátlisti fyrir sameiningu


---

*Ertu með spurningu? Búðu til issue með merkinu help-wanted*