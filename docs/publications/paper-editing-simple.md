# ✏️ Paper bearbeiten - Kurzanleitung

> **Für alle, die einfach nur Text ändern wollen - ohne Terminal, ohne Installation.**

---

## So funktioniert's (3 Schritte)

### Schritt 1: Datei öffnen

1. Gehe zu **[Paper LaTeX-Datei](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/blob/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.tex)**
2. Klicke auf **"Edit" → "Edit single file"**

![Edit Button](https://docs.gitlab.com/ee/user/project/repository/img/web_editor_edit_button_v16.png)

### Schritt 2: Änderungen machen

- Ändere den Text direkt im Editor
- LaTeX-Befehle (mit `\`) möglichst nicht anfassen
- Bei Unsicherheit: nur den Text zwischen `{}` ändern

**Beispiel:**
```latex
% VORHER
\section{Introduction}
This paper presents CLARISSA, a system for...

% NACHHER  
\section{Introduction}
This paper presents CLARISSA, an innovative system for...
```

### Schritt 3: Speichern

1. Scrolle nach unten
2. **"Target branch"**: Wähle `Create new branch`
3. Gib einen Namen ein, z.B. `paper-fix-typo-abstract`
4. ✅ Aktiviere **"Start a new merge request"**
5. Klicke **"Commit changes"**

**Fertig!** 🎉 

Ein Merge Request wird erstellt. Das Team reviewed die Änderung und baut das PDF neu.

---

## PDF automatisch bauen lassen

Nach dem Merge wird das PDF automatisch neu gebaut. Du kannst es auch manuell triggern:

1. Gehe zu **[CI/CD → Pipelines](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines)**
2. Klicke **"Run pipeline"**
3. Wähle deinen Branch
4. Klicke **"Run pipeline"**
5. Warte bis `build_paper` erscheint, klicke ▶️

Das neue PDF findest du dann unter **"Job artifacts"**.

---

## Häufige Fragen

### Kann ich das PDF direkt bearbeiten?
❌ Nein - das PDF wird aus der `.tex` Datei generiert. Änderungen am PDF gehen beim nächsten Build verloren.

### Was wenn ich einen Fehler mache?
✅ Kein Problem! Deine Änderung geht erst in einen "Merge Request" - das Team schaut drüber bevor es live geht.

### Wie ändere ich eine Abbildung?
Die Abbildungen sind PNG-Dateien in `conference/ijacsa-2026/figures/`. Du kannst sie herunterladen, bearbeiten, und als neue Datei hochladen.

### Wo sehe ich das fertige PDF?
→ **[Aktuelles PDF herunterladen](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.pdf)**

---

## Hilfe

Probleme? Erstelle ein **[Issue](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues/new)** mit Label `help-wanted`.
