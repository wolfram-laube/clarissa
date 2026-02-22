# NEXT SESSION — Live Dual-Simulator Cross-Validation on Nordic VM

## Context

The entire Sim-Engine pipeline is implemented and tested with synthetic data
(574 tests, 0 failed). Both backends (OPM Flow + MRST Octave) are PAL-compliant.
What's missing: running **real simulators** on real hardware and producing a
real `ComparisonReport` from the two independent solvers.

### Was existiert (alles getestet, alles in main/MWPS):

| Module | LOC | Tests | Status |
|--------|-----|-------|--------|
| `opm_backend.py` | 553 | 67+ | ✅ PAL-compliant |
| `mrst_backend.py` | 489 | 67+ | ✅ PAL-compliant |
| `deck_generator.py` | 387 | 38 | ✅ SimRequest → .DATA |
| `deck_parser.py` | 548 | 57 | ✅ .DATA → SimRequest |
| `eclipse_reader.py` | 382 | 37 | ✅ .SMSPEC/.UNRST → UnifiedResult |
| `mrst_script_generator.py` | 327 | 67 | ✅ SimRequest → .m |
| `comparison.py` | 479 | 58 | ✅ NRMSE/MAE/R² |
| `sim_api.py` | 307 | 31 | ✅ FastAPI gateway |
| `engine.py` | 131 | 26 | ✅ Thin SDK |

### SPE1 Reference Data
Git submodule `tests/fixtures/decks/spe1/` mit `SPE1CASE2.DATA` + INCLUDEs.
Geparst und validiert: 10×10×3 Grid, 2 Wells (INJ+PROD), FIELD units.

## Ziel der nächsten Session

**Erster echter OPM vs. MRST Cross-Validation Run auf SPE1.**

```
SPE1CASE2.DATA
     ↓
  deck_parser → SimRequest
     ↓                    ↓
  OPM Flow              MRST/Octave
  (Nordic VM)           (Nordic VM)
     ↓                    ↓
  UnifiedResult_A      UnifiedResult_B
     ↓_________↓
     compare(A, B)
         ↓
  ComparisonReport
  (NRMSE, MAE, R², per-cell, per-well)
```

## Voraussetzungen auf Nordic VM (178.156.251.191)

### OPM Flow
```bash
# Check if already installed
flow --version
# If not:
sudo apt-add-repository ppa:opm/ppa && sudo apt update
sudo apt install opm-simulators opm-common
# Verify:
flow SPE1CASE2.DATA   # should produce .SMSPEC, .UNRST, .EGRID
```

### GNU Octave + MRST
```bash
# Check
octave --version
# If not:
sudo apt install octave octave-io
# MRST Clone:
git clone https://github.com/SINTEF-AppliedCompSci/MRST.git ~/mrst
# Verify:
octave --no-gui --eval "addpath(genpath('~/mrst')); mrstModule add ad-core"
```

### Python Environment
```bash
cd ~/clarissa
pip install -e ".[dev]"  # or pip install resdata resfo scipy
python -c "from clarissa.sim_engine import SimEngine; print('OK')"
```

## Arbeitsschritte

### 1. OPM Flow auf SPE1
```bash
cd /tmp/opm-test
cp tests/fixtures/decks/spe1/SPE1CASE2.DATA .
cp tests/fixtures/decks/spe1/include/* .   # INCLUDE files
flow SPE1CASE2.DATA
ls *.SMSPEC *.UNRST   # Output vorhanden?
```

```python
from clarissa.sim_engine.eclipse_reader import read_eclipse_output
result_opm = read_eclipse_output("/tmp/opm-test/SPE1CASE2")
print(f"Timesteps: {len(result_opm.timesteps)}")
print(f"Cells: {len(result_opm.timesteps[0].cells.pressure)}")
print(f"Wells: {[w.well_name for w in result_opm.timesteps[0].wells]}")
```

### 2. MRST auf SPE1
```python
from clarissa.sim_engine.backends.mrst_backend import MRSTBackend
from clarissa.sim_engine.deck_parser import parse_deck_file, deck_to_sim_request

request = deck_to_sim_request(parse_deck_file("tests/fixtures/decks/spe1/SPE1CASE2.DATA"))
backend = MRSTBackend(mrst_root="~/mrst")
errors = backend.validate(request)
raw = backend.run(request, "/tmp/mrst-test")
result_mrst = backend.parse_result(raw, request)
```

### 3. Cross-Validation
```python
from clarissa.sim_engine.comparison import compare

report = compare(result_opm, result_mrst, "OPM Flow", "MRST Octave")
print(f"Quality: {report.match_quality}")
print(f"NRMSE:   {report.overall_nrmse:.4f}")
print(f"Cells:   {len(report.cell_metrics)}")
print(f"Wells:   {len(report.well_metrics)}")
print(report.summary())
```

### 4. Wenn das funktioniert → Docker + sim_api
```bash
docker build -t clarissa-sim -f src/clarissa/sim_engine/Dockerfile .
docker run -p 8080:8080 clarissa-sim
curl http://localhost:8080/health
```

## Erwartete Probleme

| Problem | Mitigation |
|---------|------------|
| OPM nicht installiert auf Nordic | PPA installieren, dauert 5min |
| Octave fehlt | apt install, dauert 2min |
| MRST Pfad falsch | `mrst_root` Parameter in MRSTBackend |
| INCLUDE Pfade in SPE1 relativ | Files ins gleiche Verzeichnis kopieren |
| Timestep-Mismatch OPM↔MRST | compare() hat `time_tolerance_days` |
| Memory-Limit bei größerem Grid | SPE1 ist 300 Zellen — kein Problem |

## Architektur-Kontext

ADR-040 v2 ist committed. ICE v2.1 Compliance bestätigt:
- Single PAL Registry, keine parallele State
- Unabhängige Module, keine God Class
- sim_api nutzt Registry direkt
- SimEngine ist optionaler Thin SDK

**Nicht anfassen in der nächsten Session:**
- Keine Architektur-Änderungen — die PAL steht
- Kein Refactoring — Code ist clean
- Fokus: **Execution**, nicht Design

## Key Files

```
src/clarissa/sim_engine/
├── backends/opm_backend.py         # validate/run/parse_result
├── backends/mrst_backend.py        # validate/run/parse_result
├── eclipse_reader.py               # read_eclipse_output()
├── deck_parser.py                  # parse_deck_file()
├── comparison.py                   # compare()
└── sim_api.py                      # FastAPI (für Docker)

tests/fixtures/decks/spe1/          # SPE1CASE2.DATA + INCLUDEs
```

## Nordic VM Access
```
ssh wolfram@178.156.251.191
# Docker, K3s, Python 3.12 vorhanden
# 40GB Disk, prune Sundays 04:00 UTC
```
