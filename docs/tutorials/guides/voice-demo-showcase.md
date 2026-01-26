# 🎬 Voice Input Demo - Showcase Guide

Step-by-step guide for demonstrating and recording CLARISSA's voice input feature.

---

## 🎯 What You'll Show

1. **Voice Recognition** - Speaking naturally to the interface
2. **Real-time Transcription** - Text appears as you speak
3. **AI Response** - CLARISSA answers reservoir engineering questions
4. **Visualizations** - Audio waveform and analysis displays

---

## 📋 Before Recording

### 1. Open the Demo
```
https://irena-40cc50.gitlab.io/demos/voice-demo.html
```

### 2. Enter API Key
- Click the key icon (🔑) or settings
- Enter your OpenAI API key
- Key is stored locally in browser (never sent to our servers)

### 3. Test Audio
- Click 🎤 once to test microphone access
- Browser will ask for permission - **Allow**
- Speak briefly to verify levels

### 4. Start Recording Tool
```bash
# Terminal: 60 second recording with camera
record-pip.sh start 60

# Or browser-based:
# Open https://irena-40cc50.gitlab.io/demos/screen-recorder-pip.html
```

---

## 🎤 Demo Script (Suggested)

### Opening (5 sec)
> "This is CLARISSA's voice input interface for reservoir simulation."

### Show the Interface (10 sec)
- Point out the microphone button
- Show the example buttons at the bottom
- Mention the visualization area

### Demo 1: Use Example Button (15 sec)
1. Click an example button, e.g., **"What is water saturation?"**
2. Watch the text appear in the input field
3. See CLARISSA's response appear
4. Point out the response quality

### Demo 2: Voice Input (20 sec)
1. Click 🎤 microphone button (or press **Space**)
2. **Speak clearly:** 
   > "How do I calculate pore volume in a reservoir simulation?"
3. Watch real-time transcription
4. Release button (or press Space again)
5. See response generate

### Demo 3: Follow-up Question (15 sec)
1. Click 🎤 again
2. **Ask follow-up:**
   > "What units should I use for that?"
3. Show conversational context is maintained

### Closing (5 sec)
> "Voice input makes reservoir simulation more accessible."

---

## 💬 Example Questions to Ask

### Beginner-friendly
- "What is porosity?"
- "Explain water saturation"
- "What's the difference between oil and gas reservoirs?"

### Technical
- "How do I set up a waterflood simulation?"
- "What keywords do I need for relative permeability?"
- "Explain the WELSPECS keyword in Eclipse"

### Practical
- "How do I define a new injection well?"
- "What causes convergence problems in simulation?"
- "How should I set timestep controls?"

---

## 📊 What to Expect in Response

### Text Response
- Clear, structured answer
- Relevant to reservoir engineering
- May include code snippets for keywords

### Visualizations (when enabled)
- **Audio Waveform**: Shows your speech pattern
- **Transcription Confidence**: How certain the recognition was
- **Response Time**: Processing latency

### Example Response Format
```
Question: "How is pore volume calculated?"

Answer: Pore volume (PV) is calculated as:

PV = Bulk Volume × Porosity × Net-to-Gross

Where:
- Bulk Volume: Total rock volume (e.g., from grid cells)
- Porosity: Fraction of void space (0-1)
- Net-to-Gross: Fraction that is reservoir rock

In Eclipse, you can use the PORV keyword to see 
calculated pore volumes, or MULTPV to apply multipliers.
```

---

## 🎥 Recording Tips

### Camera Position (for PiP)
- Face visible in corner
- Good lighting on face
- Neutral background

### Audio
- Quiet environment
- Speak at normal pace
- Pause briefly between actions

### Screen
- Browser in focus, full width
- Hide bookmarks bar for cleaner look
- Close unnecessary tabs

### Timing
- 60 seconds is ideal for a quick demo
- 2-3 minutes for comprehensive showcase
- Keep individual segments under 20 seconds

---

## 🔧 Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Mic not working | Refresh page, re-allow permission |
| No transcription | Check API key is entered |
| Slow response | Normal - wait for AI processing |
| Recognition errors | Speak slower, closer to mic |

---

## 📁 After Recording

### Files Location
- **macOS:** `~/Movies/CLARISSA-Demos/`
- **Linux:** `~/Videos/CLARISSA-Demos/`

### Suggested Naming
```
CLARISSA-Voice-Demo-2026-01-25.mp4
CLARISSA-Voice-Quickstart-60s.mp4
```

### Sharing
- Upload to GitLab/Google Drive
- Link in documentation or issues
- Attach to SPE paper supplementary materials

---

## 📚 Related Resources

- [Voice Input Tutorial](voice-input-tutorial.md) - Detailed technical guide
- [Recording Tools](../../tools/recording/README.md) - All recording options
- [ADR-028](../../architecture/decisions/adr-028-voice-input-architecture.md) - Architecture details

---

*Part of [CLARISSA](https://gitlab.com/wolfram_laube/blauweiss_llc/irena) - Conversational Language Agent for Reservoir Simulation*
