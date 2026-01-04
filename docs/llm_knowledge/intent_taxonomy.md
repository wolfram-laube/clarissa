# Intent Taxonomy Reference

Vollständige Referenz der CLARISSA Intent-Taxonomie für Reviews.

## Kategorien

### 1. simulation_control

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `RUN_SIMULATION` | Simulation starten | "run simulation", "execute CASE1", "start the model" |
| `STOP_SIMULATION` | Simulation stoppen | "stop the run", "halt simulation", "abort" |
| `RESTART_SIMULATION` | Von Checkpoint fortsetzen | "restart from June", "continue simulation" |

**Required Entities:** (none für RUN)
**Optional Entities:** `target_date` (für RESTART)

---

### 2. well_operations

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `ADD_WELL` | Neuen Well definieren | "add producer PROD-01", "create new injector" |
| `MODIFY_WELL` | Well-Parameter ändern | "modify PROD-01 completions", "change well" |
| `SHUT_WELL` | Well schließen | "shut PROD-01", "close well INJ-A" |
| `OPEN_WELL` | Well öffnen | "open PROD-01", "bring INJ-A online" |
| `SET_RATE` | Rate setzen | "set rate to 500 bbl/day", "change oil rate" |
| `SET_PRESSURE` | Druck setzen | "set BHP to 2000 psi", "target pressure 150 bar" |

**Required Entities:**
- `ADD_WELL`: `well_name`, `well_type`
- `SHUT_WELL`: `well_name`
- `SET_RATE`: `well_name`, `rate_value`, `rate_unit`
- `SET_PRESSURE`: `well_name`, `pressure_value`, `pressure_unit`

---

### 3. schedule_operations

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `SET_DATE` | Zu Datum springen | "go to January 2025", "advance to June" |
| `ADD_TIMESTEP` | Zeitschritt hinzufügen | "add 30 days", "step 6 months forward" |
| `MODIFY_SCHEDULE` | Schedule ändern | "change schedule", "adjust timeline" |

**Required Entities:**
- `SET_DATE`: `target_date`
- `ADD_TIMESTEP`: `timestep_size`, `timestep_unit`

---

### 4. query_operations

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `GET_PRODUCTION` | Produktionsdaten abfragen | "show oil production", "what's the water cut" |
| `GET_PRESSURE` | Druckdaten abfragen | "what's the BHP", "show reservoir pressure" |
| `GET_SATURATION` | Sättigungen abfragen | "show water saturation", "what's the Sw" |
| `GET_WELLS` | Well-Liste abfragen | "list all wells", "show producers" |
| `GET_SCHEDULE` | Schedule abfragen | "show schedule", "what's planned" |

**Required Entities:** (meist keine - Kontext aus Dialog)
**Optional Entities:** `well_name`, `phase`, `target_date`

---

### 5. validation

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `VALIDATE_DECK` | Deck-Syntax prüfen | "validate deck", "check syntax" |
| `CHECK_CONVERGENCE` | Konvergenz prüfen | "check convergence", "is it stable" |
| `VALIDATE_PHYSICS` | Physik-Konsistenz | "validate physics", "check material balance" |

**Required Entities:** (keine)

---

### 6. help_and_info

| Intent | Beschreibung | Beispiel-Phrases |
|--------|--------------|------------------|
| `GET_HELP` | Hilfe anfordern | "help", "how do I...", "what can you do" |
| `EXPLAIN_KEYWORD` | Keyword erklären | "explain WCONPROD", "what does COMPDAT do" |
| `LIST_KEYWORDS` | Keywords auflisten | "list keywords", "show available commands" |

**Required Entities:**
- `EXPLAIN_KEYWORD`: keyword name (zu extrahieren)

---

## Entity-Definitionen

### well_name
- **Pattern:** `[A-Z][A-Z0-9_-]*` oder quoted string
- **Beispiele:** PROD-01, INJ_A, P1, 'WELL 1'
- **Validation:** Muss im Asset-Inventory existieren

### rate_value + rate_unit
- **Pattern:** `\d+(\.\d+)?` + `(bbl|STB|BBL|m3|SM3)/d(ay)?`
- **Beispiele:** 500 bbl/day, 1000 STB/d, 100 m3/day
- **Conversion:** Alles zu STB/day normalisieren

### pressure_value + pressure_unit
- **Pattern:** `\d+(\.\d+)?` + `(psi|bar|kPa|MPa)`
- **Beispiele:** 2000 psi, 150 bar, 10000 kPa
- **Conversion:** Alles zu psia normalisieren

### target_date
- **Patterns:**
  - ISO: `2025-06-15`
  - Month-Year: `January 2025`, `Jan 2025`
  - Relative: `next month`, `in 30 days`
- **Output:** ISO format

### timestep_size + timestep_unit
- **Pattern:** `\d+` + `(day|week|month|year)s?`
- **Beispiele:** 30 days, 6 months, 1 year

### phase
- **Values:** oil, water, gas, liquid
- **Case-insensitive**

### well_type
- **Values:** producer, injector
- **Aliases:** prod → producer, inj → injector

### grid_location
- **Pattern:** `I\s*=\s*\d+` and/or `J\s*=\s*\d+` and/or `K\s*=\s*\d+`
- **Beispiele:** I=10 J=15, I=5 J=5 K=1

---

## Offene Fragen (für Review)

1. **Fehlende Intents?**
   - Aquifer operations?
   - PVT modifications?
   - Grid refinement?
   - Group operations?

2. **Fehlende Entities?**
   - Permeability?
   - Porosity?
   - Formation name?
   - Fluid contacts?

3. **Pattern-Verbesserungen?**
   - Welche Phrasen fehlen?
   - Welche sind zu broad/narrow?