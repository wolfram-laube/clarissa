#!/bin/bash
# ============================================
# 🎬 CLARISSA Demo Recording Tools Setup
# ============================================
# Installiert 3 verschiedene Aufnahme-Varianten
# zum Evaluieren auf dem Mac

OUTPUT_DIR=~/Movies/CLARISSA-Demos
SCRIPTS_DIR=~/bin
mkdir -p "$OUTPUT_DIR" "$SCRIPTS_DIR"

echo "🎬 CLARISSA Demo Recording Tools"
echo "================================="
echo ""

# ============================================
# Option A: AppleScript (steuert QuickTime)
# ============================================
cat << 'EOF' > "$SCRIPTS_DIR/record-a-applescript.sh"
#!/bin/bash
# Option A: AppleScript - Steuert QuickTime Player
# Pro: Native macOS Qualität, einfach
# Con: Braucht GUI-Interaktion für Mikrofon-Auswahl

ACTION=${1:-help}
OUTPUT_DIR=~/Movies/CLARISSA-Demos
mkdir -p "$OUTPUT_DIR"

case "$ACTION" in
    start)
        echo "🔴 Starting QuickTime screen recording..."
        echo "   ⚠️  Klick 'Optionen' und wähl dein Mikrofon!"
        osascript << 'APPLESCRIPT'
tell application "QuickTime Player"
    activate
    new screen recording
    delay 0.5
end tell
APPLESCRIPT
        echo ""
        echo "   → Klick den roten Aufnahme-Button in QuickTime"
        echo "   → Zum Stoppen: Klick ⏹️ in der Menüleiste"
        echo "   → Oder: $0 stop"
        ;;
        
    stop)
        echo "⏹️  Stopping QuickTime recording..."
        osascript << 'APPLESCRIPT'
tell application "QuickTime Player"
    stop document 1
end tell
APPLESCRIPT
        echo "✅ Recording gestoppt - QuickTime fragt nach Speicherort"
        ;;
        
    *)
        echo "Usage: $0 [start|stop]"
        echo ""
        echo "Option A: AppleScript/QuickTime"
        echo "  + Native macOS Qualität"
        echo "  + Einfache Bedienung"  
        echo "  - Mikrofon muss manuell gewählt werden"
        echo "  - Speicherort wird am Ende abgefragt"
        ;;
esac
EOF
chmod +x "$SCRIPTS_DIR/record-a-applescript.sh"
echo "✅ Option A: $SCRIPTS_DIR/record-a-applescript.sh"

# ============================================
# Option B: ffmpeg mit Start/Stop
# ============================================
cat << 'EOF' > "$SCRIPTS_DIR/record-b-ffmpeg.sh"
#!/bin/bash
# Option B: ffmpeg mit Start/Stop Toggle
# Pro: Volle Kontrolle, automatisches Speichern
# Con: Braucht ffmpeg Installation

OUTPUT_DIR=~/Movies/CLARISSA-Demos
mkdir -p "$OUTPUT_DIR"
PIDFILE=/tmp/clarissa-record.pid
OUTFILE=/tmp/clarissa-record-output.txt

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg nicht installiert!"
    echo "   Installieren mit: brew install ffmpeg"
    exit 1
fi

case "${1:-toggle}" in
    start)
        if [ -f "$PIDFILE" ]; then
            echo "⚠️  Läuft bereits! PID: $(cat $PIDFILE)"
            echo "   Stoppen mit: $0 stop"
            exit 1
        fi
        
        OUTPUT="$OUTPUT_DIR/demo-$(date +%Y%m%d-%H%M%S).mp4"
        echo "$OUTPUT" > "$OUTFILE"
        
        echo "🔴 Recording gestartet..."
        echo "   Output: $OUTPUT"
        echo ""
        echo "   Stoppen mit: $0 stop"
        echo "   Oder:        $0 toggle"
        
        # Screen: "1" = Hauptbildschirm, Audio: "0" = Default Mikrofon
        # Liste Geräte: ffmpeg -f avfoundation -list_devices true -i ""
        nohup ffmpeg -f avfoundation -framerate 30 \
               -capture_cursor 1 \
               -i "1:0" \
               -c:v h264 -crf 23 -preset fast \
               -c:a aac -b:a 128k \
               -y "$OUTPUT" \
               > /tmp/ffmpeg-record.log 2>&1 &
        
        echo $! > "$PIDFILE"
        sleep 1
        
        if ps -p $(cat "$PIDFILE") > /dev/null 2>&1; then
            echo "🎬 Recording läuft (PID: $(cat $PIDFILE))"
        else
            echo "❌ ffmpeg konnte nicht starten. Log:"
            tail -5 /tmp/ffmpeg-record.log
            rm -f "$PIDFILE"
        fi
        ;;
        
    stop)
        if [ ! -f "$PIDFILE" ]; then
            echo "⚠️  Keine Aufnahme aktiv"
            exit 1
        fi
        
        PID=$(cat "$PIDFILE")
        OUTPUT=$(cat "$OUTFILE" 2>/dev/null)
        
        echo "⏹️  Stopping recording (PID: $PID)..."
        kill -INT $PID 2>/dev/null
        
        # Warte auf sauberes Ende
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        
        rm -f "$PIDFILE" "$OUTFILE"
        
        if [ -f "$OUTPUT" ]; then
            SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
            echo "✅ Gespeichert: $OUTPUT ($SIZE)"
            echo ""
            read -p "   Video öffnen? [Y/n] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                open "$OUTPUT"
            fi
        else
            echo "⚠️  Output-Datei nicht gefunden"
        fi
        ;;
        
    toggle)
        if [ -f "$PIDFILE" ]; then
            $0 stop
        else
            $0 start
        fi
        ;;
        
    status)
        if [ -f "$PIDFILE" ] && ps -p $(cat "$PIDFILE") > /dev/null 2>&1; then
            echo "🔴 Recording läuft (PID: $(cat $PIDFILE))"
            echo "   Output: $(cat $OUTFILE 2>/dev/null)"
        else
            echo "⚪ Keine Aufnahme aktiv"
            rm -f "$PIDFILE" "$OUTFILE" 2>/dev/null
        fi
        ;;
        
    devices)
        echo "📹 Verfügbare Geräte:"
        ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -E "^\[AVFoundation"
        ;;
        
    *)
        echo "Usage: $0 [start|stop|toggle|status|devices]"
        echo ""
        echo "Option B: ffmpeg Start/Stop"
        echo "  + Volle Kontrolle"
        echo "  + Automatisches Speichern"
        echo "  + Toggle-Funktion"
        echo "  - Braucht ffmpeg (brew install ffmpeg)"
        ;;
esac
EOF
chmod +x "$SCRIPTS_DIR/record-b-ffmpeg.sh"
echo "✅ Option B: $SCRIPTS_DIR/record-b-ffmpeg.sh"

# ============================================
# Option C: ffmpeg mit Timer
# ============================================
cat << 'EOF' > "$SCRIPTS_DIR/record-c-timed.sh"
#!/bin/bash
# Option C: ffmpeg mit Zeitlimit (fire & forget)
# Pro: Einfachste Bedienung, öffnet Video automatisch
# Con: Feste Dauer, braucht ffmpeg

DURATION=${1:-60}
OUTPUT_DIR=~/Movies/CLARISSA-Demos
mkdir -p "$OUTPUT_DIR"
OUTPUT="$OUTPUT_DIR/demo-$(date +%Y%m%d-%H%M%S).mp4"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg nicht installiert!"
    echo "   Installieren mit: brew install ffmpeg"
    exit 1
fi

# Hilfe
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [SEKUNDEN]"
    echo ""
    echo "Option C: Timed Recording"
    echo "  + Fire & forget"
    echo "  + Öffnet Video automatisch"
    echo "  + Ctrl+C zum vorzeitigen Stoppen"
    echo "  - Feste Aufnahmedauer"
    echo ""
    echo "Beispiele:"
    echo "  $0 30    # 30 Sekunden"
    echo "  $0 120   # 2 Minuten"
    echo "  $0       # 60 Sekunden (default)"
    exit 0
fi

echo "🎬 ================================================"
echo "   CLARISSA Demo Recording"
echo "   ================================================"
echo ""
echo "   ⏱️  Dauer:  $DURATION Sekunden"
echo "   📁 Output: $OUTPUT"
echo ""
echo "   🔴 Recording startet in 3 Sekunden..."
echo "   (Ctrl+C zum vorzeitigen Stoppen)"
echo ""

# Countdown
for i in 3 2 1; do
    echo "   $i..."
    sleep 1
done

echo ""
echo "   🔴 RECORDING!"
echo ""

# Aufnahme mit Progress
ffmpeg -f avfoundation -framerate 30 \
       -capture_cursor 1 \
       -t $DURATION \
       -i "1:0" \
       -c:v h264 -crf 23 -preset fast \
       -c:a aac -b:a 128k \
       -y "$OUTPUT" \
       2>&1 | grep --line-buffered "time=" | while read line; do
           TIME=$(echo "$line" | grep -oE "time=[0-9:.]+" | cut -d= -f2)
           echo -ne "\r   ⏱️  $TIME / $(printf '%02d:%02d' $((DURATION/60)) $((DURATION%60)))   "
       done

echo ""
echo ""

if [ -f "$OUTPUT" ]; then
    SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
    DURATION_ACTUAL=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null | cut -d. -f1)
    
    echo "   ✅ Recording fertig!"
    echo "   📁 $OUTPUT"
    echo "   📊 Größe: $SIZE, Dauer: ${DURATION_ACTUAL}s"
    echo ""
    
    # Video öffnen
    open "$OUTPUT"
else
    echo "   ❌ Recording fehlgeschlagen"
    exit 1
fi
EOF
chmod +x "$SCRIPTS_DIR/record-c-timed.sh"
echo "✅ Option C: $SCRIPTS_DIR/record-c-timed.sh"

# ============================================
# Convenience Wrapper
# ============================================
cat << 'EOF' > "$SCRIPTS_DIR/record-demo.sh record-pip.sh"
#!/bin/bash
# Convenience Wrapper - wähle deine bevorzugte Methode

echo "🎬 CLARISSA Demo Recording"
echo "=========================="
echo ""
echo "Welche Methode?"
echo ""
echo "  A) AppleScript/QuickTime (native, GUI)"
echo "  B) ffmpeg Start/Stop (flexibel)"
echo "  C) ffmpeg Timed (einfach)"
echo ""
read -p "Wahl [A/B/C]: " -n 1 choice
echo ""
echo ""

case "$choice" in
    [Aa]) ~/bin/record-a-applescript.sh start ;;
    [Bb]) ~/bin/record-b-ffmpeg.sh toggle ;;
    [Cc]) 
        read -p "Wie viele Sekunden? [60]: " duration
        ~/bin/record-c-timed.sh ${duration:-60}
        ;;
    *) echo "Ungültige Wahl" ;;
esac
EOF
chmod +x "$SCRIPTS_DIR/record-demo.sh record-pip.sh"
echo "✅ Wrapper:  $SCRIPTS_DIR/record-demo.sh record-pip.sh"

# ============================================
# PATH Setup
# ============================================
echo ""
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "📌 Füge ~/bin zu PATH hinzu..."
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    echo "   (Neu starten oder 'source ~/.zshrc' ausführen)"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "============================================"
echo "🎉 Installation fertig!"
echo "============================================"
echo ""
echo "📁 Scripts in: $SCRIPTS_DIR/"
echo "📁 Videos in:  $OUTPUT_DIR/"
echo ""
echo "Verwendung:"
echo ""
echo "  Option A (QuickTime):"
echo "    record-a-applescript.sh start"
echo "    record-a-applescript.sh stop"
echo ""
echo "  Option B (ffmpeg toggle):"
echo "    record-b-ffmpeg.sh start"
echo "    record-b-ffmpeg.sh stop"
echo "    record-b-ffmpeg.sh toggle"
echo "    record-b-ffmpeg.sh status"
echo ""
echo "  Option C (ffmpeg timed):"
echo "    record-c-timed.sh 30      # 30 Sekunden"
echo "    record-c-timed.sh 120     # 2 Minuten"
echo ""
echo "  Oder interaktiv:"
echo "    record-demo.sh record-pip.sh"
echo ""
echo "============================================"
echo ""

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg nicht installiert (Option B & C brauchen es)"
    echo "   Installieren: brew install ffmpeg"
    echo ""
fi
