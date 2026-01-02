# 🦊 CLARISSA GitLab Verkflæði - Þjöppuð leiðbeining

> **Í stuttu máli:** Issue → Grein → Commit → MR → Sameina → Issue lokast sjálfkrafa

---

## 🔄 Verkflæðið í 5 skrefum

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Veldu   │───▶│  2. Búðu    │───▶│ 3. Commit  │───▶│  4. Búðu    │───▶│ 5. Rýni &  │
│    Issue    │    │  til grein  │    │   & Push   │    │   til MR    │    │  sameining │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 1️⃣ Veldu Issue af borðinu

```
Project → Plan → Issue Boards
```

- Taktu issue úr **Ready** dálkinum
- Færðu í **In Progress**

---

## 2️⃣ Búðu til grein

```bash
# ALLTAF byrja á issue-númeri!
git checkout -b 42-stutt-lysing
```

| ✅ Gott | ❌ Slæmt |
|---------|----------|
| `42-add-login` | `my-branch` |
| `12-fix-bug` | `test123` |
| `7-update-docs` | `changes` |

---

## 3️⃣ Commit með issue-tilvísun

```bash
git commit -m "type: lýsing #42"
```

### Conventional Commits forskeyti:

| Forskeyti | Notkun |
|-----------|--------|
| `feat:` | Nýr eiginleiki |
| `fix:` | Villuleiðrétting |
| `docs:` | Skjölun |
| `chore:` | Viðhald |
| `refactor:` | Endurskipulagning |
| `test:` | Prófanir |

### Dæmi:

```bash
git commit -m "feat: bæta við notandavottun #42"
git commit -m "fix: laga null pointer villu #15"
git commit -m "docs: uppfæra leiðbeiningar #7"
```

---

## 4️⃣ Búðu til Merge Request

```bash
git push -u origin 42-stutt-lysing
```

### MR-lýsing sniðmát:

```markdown
## Samantekt
Stutt lýsing á breytingum.

## Breytingar
- Atriði 1
- Atriði 2

## Tengt
Closes #42

## Gátlisti
- [ ] Kóði prófaður
- [ ] Skjölun uppfærð
```

**Mikilvægt:** `Closes #42` lokar issue sjálfkrafa við sameiningu!

---

## 5️⃣ Rýni & sameining

1. Rýnir skoðar kóða
2. Þegar samþykkt: Smelltu á **Merge**
3. ✅ Issue lokast sjálfkrafa!

---

## 🔗 Töfraorðin

Þessi orð í commit eða MR loka issues sjálfkrafa:

| Orð | Áhrif |
|-----|-------|
| `Closes #42` | Lokar issue við sameiningu |
| `Fixes #42` | Lokar issue við sameiningu |
| `Resolves #42` | Lokar issue við sameiningu |
| `#42` | Bara tenging |

---

## 🚫 Bannað

1. ❌ Push beint á `main`
2. ❌ Commit án issue-tilvísunar (`#42`)
3. ❌ Commit leyniorð/secrets
4. ❌ Risastórt MR með 50 skrám
5. ❌ MR án `Closes #X`

---

## ✅ Gátlisti fyrir sameiningu

- [ ] Greinarheiti inniheldur issue-númer
- [ ] Commit fylgja Conventional Commits
- [ ] Commit vísa í issue (`#42`)
- [ ] MR hefur `Closes #42`
- [ ] CI pipeline grænt
- [ ] Issue merki stillt á `workflow::review`

---

## 🔗 Flýtitenglar

| Auðlind | Slóð |
|---------|------|
| Verkefnaborð | `/-/boards` |
| Öll Issues | `/-/issues` |
| Merge Requests | `/-/merge_requests` |
| Gagnvirk kynning | `docs/guides/contributing/workflow-slides-is.html` |

---

*Ertu með spurningu? Búðu til issue með merkinu `help-wanted`*
