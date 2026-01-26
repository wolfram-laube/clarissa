# 🎬 CLARISSA Voice Demo - Showcase Guide

Anleitung zum Aufnehmen eines überzeugenden Voice Input Demo-Videos.

---

## 🎯 Was wir zeigen wollen

1. **Voice Input funktioniert** - Sprechen → Transkription → Antwort
2. **Reservoir Engineering Kontext** - Fachspezifische Fragen werden verstanden
3. **Interaktive Visualisierung** - Audio-Wellenform während der Spracheingabe

---

## 📋 Vorbereitung

### 1. API Key bereithalten
- OpenAI API Key (für Whisper + GPT)
- Alternativ: Den Demo-Mode ohne Key nutzen (limitiert)

### 2. Browser vorbereiten
- **Chrome oder Edge** (WebSpeech API Support)
- Mikrofon-Berechtigung erteilen
- Tabs schließen die stören könnten

### 3. Recording Tool starten
```bash
# Terminal öffnen, dann:
record-pip.sh start 90    # 90 Sekunden mit Kamera

# Oder Browser-Recorder:
# https://irena-40cc50.gitlab.io/demos/screen-recorder-pip.html
```

### 4. Demo öffnen
```
https://irena-40cc50.gitlab.io/demos/voice-demo.html
```

---

## 🎬 Aufnahme-Ablauf (Empfohlen: 60-90 Sekunden)

### Phase 1: Setup (0:00 - 0:15)
**Was tun:**
- Demo-Seite ist bereits offen
- API Key eingeben (oder zeigen dass er schon drin ist)
- Kurz die UI erklären: "Hier ist das CLARISSA Voice Interface..."

**Was sagen:**
> "Ich zeige euch jetzt das CLARISSA Voice Input Feature. 
> Man gibt seinen API Key ein und kann dann per Sprache 
> Reservoir Engineering Fragen stellen."

### Phase 2: Erste Spracheingabe (0:15 - 0:35)
**Was tun:**
1. Auf 🎤 Mikrofon-Button klicken
2. Warten bis "Listening..." erscheint
3. Klar und deutlich sprechen
4. Button erneut klicken zum Stoppen

**Beispiel-Fragen (einfach → komplex):**

| Schwierigkeit | Frage |
|---------------|-------|
| Einfach | *"What is porosity?"* |
| Mittel | *"Explain the difference between oil-wet and water-wet reservoirs."* |
| Fortgeschritten | *"How do I set up a five-spot waterflood pattern in Eclipse?"* |

**Was im Interface passiert:**
- 🟢 Grüner Kreis pulsiert während Aufnahme
- 📊 Audio-Wellenform visualisiert Sprachlautstärke
- 📝 Live-Transkription erscheint während des Sprechens

### Phase 3: Antwort zeigen (0:35 - 0:55)
**Was passiert:**
- "Processing..." erscheint kurz
- Antwort wird in der Chat-Box angezeigt
- Bei Code-Fragen: Syntax-highlighted Code-Blöcke

**Was erwarten:**
```
┌─────────────────────────────────────────┐
│ 🎤 You asked:                           │
│ "What is porosity?"                     │
├─────────────────────────────────────────┤
│ 🤖 CLARISSA:                            │
│ Porosity is the measure of void space  │
│ in a rock, expressed as a percentage   │
│ of the total rock volume. It indicates │
│ the storage capacity for fluids...     │
│                                         │
│ Formula: φ = Vp/Vt × 100%              │
└─────────────────────────────────────────┘
```

### Phase 4: Zweite Frage (optional, 0:55 - 1:20)
**Was tun:**
- Komplexere Follow-up Frage stellen
- Zeigt Konversations-Fähigkeit

**Gute Follow-ups:**
- *"How does that affect oil recovery?"*
- *"Can you show me the Eclipse keyword for that?"*
- *"What's a typical value for sandstone?"*

### Phase 5: Abschluss (1:20 - 1:30)
**Was sagen:**
> "So einfach kann man mit CLARISSA per Sprache interagieren.
> Das Feature ist Teil unserer Phase 1 Implementierung."

---

## 🎤 Sprach-Tipps

### Do's ✅
- Klar und in normalem Tempo sprechen
- Kurze Pause nach dem Klick auf 🎤
- Fachbegriffe deutlich aussprechen
- Englisch für beste Erkennung

### Don'ts ❌
- Nicht zu schnell sprechen
- Keine Hintergrundgeräusche
- Nicht zu nah am Mikrofon (Popping)
- Nicht während Processing sprechen

---

## 📊 Was die Visualisierung zeigt

### Audio Waveform
```
     ▂▄▆█▆▄▂   ▂▄▆▇█▇▆▄▂
    ▁▃▅▇███▇▅▃▁▃▅▇█████▇▅▃▁
Zeit ──────────────────────────►
       "What"    "is porosity"
```
- Höhe = Lautstärke
- Bewegung = Echtzeit-Audio
- Hilft beim Timing

### Status-Anzeige
| Status | Bedeutung |
|--------|-----------|
| 🔵 Ready | Bereit für Eingabe |
| 🟢 Listening | Nimmt auf |
| 🟡 Processing | Transkribiert/Generiert |
| ✅ Complete | Antwort fertig |

---

## 🎯 Gute Demo-Fragen nach Thema

### Grundlagen
- *"What is permeability and how is it measured?"*
- *"Explain Darcy's law in simple terms."*
- *"What's the difference between primary and secondary recovery?"*

### Simulation-spezifisch
- *"How do I define relative permeability curves in OPM Flow?"*
- *"What keywords control well constraints in Eclipse?"*
- *"Explain the EQUIL keyword."*

### Praxis-orientiert
- *"My waterflood isn't converging. What should I check?"*
- *"How do I set up a history match workflow?"*
- *"What's a reasonable time step for a black oil model?"*

---

## 📁 Nach der Aufnahme

### Output Location
- **macOS:** `~/Movies/CLARISSA-Demos/demo-pip-*.mp4`
- **Linux:** `~/Videos/CLARISSA-Demos/demo-pip-*.mp4`

### Post-Processing (optional)
```bash
# Trim ersten/letzten 2 Sekunden
ffmpeg -i demo-pip-*.mp4 -ss 2 -t 86 -c copy demo-trimmed.mp4

# Zu GIF konvertieren (für GitLab README)
ffmpeg -i demo-trimmed.mp4 -vf "fps=10,scale=800:-1" -t 15 demo-preview.gif
```

### Wo hochladen
- GitLab Issue #66 (Voice Input Epic)
- Team Google Drive
- Direkt in Docs einbetten

---

## 🎥 Beispiel-Skript (60 Sekunden)

```
[0:00] Demo öffnet sich, API Key ist eingegeben
       "Das ist das CLARISSA Voice Interface."

[0:08] Klick auf Mikrofon
       "Ich stelle jetzt eine Frage per Sprache..."

[0:12] Sprechen: "What is the purpose of the EQUIL keyword?"

[0:18] Stop-Klick, Processing läuft
       [Stille, Waveform zeigt Verarbeitung]

[0:22] Antwort erscheint
       "Die Antwort erklärt das EQUIL Keyword..."

[0:35] Scroll durch Antwort falls nötig
       "...inklusive Beispiel-Syntax."

[0:42] Klick auf Mikrofon für Follow-up
       Sprechen: "Show me an example with gas-oil contact."

[0:50] Antwort mit Code-Block erscheint
       "CLARISSA liefert auch Code-Beispiele."

[0:58] Zoom out / Abschluss
       "So funktioniert Voice Input in CLARISSA."
```

---

## 🔗 Relevante Links

- [Voice Demo](https://irena-40cc50.gitlab.io/demos/voice-demo.html)
- [Recording Tools](../tools/recording/README.md)
- [Voice Input Tutorial](guides/voice-input-tutorial.md)
- [ADR-028 Voice Architecture](../architecture/decisions/adr-028-voice-input-architecture.md)

---

*Teil von [CLARISSA](https://gitlab.com/wolfram_laube/blauweiss_llc/irena) - Conversational Language Agent for Reservoir Simulation*
