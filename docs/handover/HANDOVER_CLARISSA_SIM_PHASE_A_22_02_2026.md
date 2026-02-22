# HANDOVER — CLARISSA Sim-Engine Phase A (22.02.2026)

## Session Summary
Implemented the three core Phase A issues for the CLARISSA Sim-Engine:
- **#164** Eclipse Deck Generator
- **#163** OPM Flow Backend (SimulatorBackend implementation)
- **#165** Sim-Engine FastAPI Service + Dockerfile

## What Was Built

### #164 — `deck_generator.py` (250 LOC)
Converts `SimRequest` Pydantic models → Eclipse `.DATA` deck format:
- Full section generation: RUNSPEC, GRID, PROPS, SOLUTION, SUMMARY, SCHEDULE
- SI → FIELD unit conversion (m→ft, bar→psi, m³/day→STB/day)
- Two-phase (oil-water) and three-phase (oil-water-gas) support
- Configurable wells: injectors (WCONINJE) + producers (WCONPROD)
- Simplified Corey-type relative permeability tables
- `generate_deck()` returns string, `write_deck()` writes to file

### #163 — `opm_backend.py` (350 LOC)
`OPMBackend(SimulatorBackend)` — complete SimulatorBackend implementation:
- `validate()`: grid size limits (100k cells), well bounds, timestep checks
- `run()`: generates deck → runs `flow` binary (subprocess) → collects output files
- `parse_result()`: reads `.UNRST` via `opm.io.ecl.ERst`, `.SMSPEC` via `ESmry`
  - Per-cell: PRESSURE, SWAT, SGAS at each report step
  - Per-well: WOPR, WWPR, WBHP, WWIR, cumulative production
  - Merges restart + summary data into `UnifiedResult`
- Docker mode support (`use_docker=True`)
- Progress callbacks (0→10→80→90→100%)

### #165 — `sim_api.py` (200 LOC) + `Dockerfile`
FastAPI service with async job queue:
- `POST /sim/run` → submit job (BackgroundTasks)
- `GET /sim/{job_id}` → poll status + progress
- `GET /sim/{job_id}/result` → full UnifiedResult JSON
- `GET /sim/list` → recent jobs
- `GET /health` → backends + capacity
- Lifespan-based startup (auto-registers OPM backend)
- CORS middleware, rate limiting (MAX_CONCURRENT_JOBS)
- Dockerfile: Ubuntu 24 + OPM PPA + Python (multi-stage)

## Test Results
- **59 new Phase A tests** (`test_sim_engine_phase_a.py`)
  - 3 unit conversion tests
  - 16 deck generator tests (incl. edge cases)
  - 4 OPM backend metadata tests
  - 7 validation tests
  - 5 run() tests (mocked subprocess)
  - 2 parse_result tests
  - 5 SPE1 reference data tests (real opm.io parsing!)
  - 4 API endpoint tests
  - 2 mock backend integration tests
  - 5 deck generator edge cases
  - 6 helper method tests
- **31 existing sim_engine tests** — all passing
- **244 total CLARISSA tests** passing (6 skipped, 2 pre-existing relay failures)

### SPE1 Reference Validation ✅
Successfully parsed OPM reference output for SPE1CASE1:
- Grid: 10×10×3 = 300 cells
- 121 report steps, 3650 days (10 years)
- PRESSURE: 4782–4800 psia (initial) → 3188–4032 psia (final)
- FOPR: 20,000 STB/day (initial) → 5,558 STB/day (final) ✅
- WBHP:PROD minimum: 1,000 psia (matches BHP limit) ✅
- SGAS: 0–0.55 at final step (gas injection confirmed) ✅

## Files Created/Modified

### CLARISSA Repo (77260390)
```
NEW:  src/clarissa/sim_engine/deck_generator.py    # #164
NEW:  src/clarissa/sim_engine/backends/opm_backend.py  # #163
NEW:  src/clarissa/sim_engine/sim_api.py           # #165
NEW:  src/clarissa/sim_engine/Dockerfile           # #165
NEW:  tests/test_sim_engine_phase_a.py             # 59 tests
MOD:  src/clarissa/sim_engine/__init__.py          # New exports
```

## OPM Python Bindings — Correct Import Paths
```python
from opm.io.ecl import ERst, ESmry, EGrid, EclFile  # NOT from opm.io directly!
rst = ERst("/path/to/CASE.UNRST")
steps = rst.report_steps  # [0, 1, 2, ..., 120]
pressure = rst['PRESSURE', step_idx]  # numpy array, len=n_cells

smry = ESmry("/path/to/CASE.SMSPEC")  # Must be .SMSPEC path!
fopr = smry['FOPR']  # Field oil production rate
wbhp = smry['WBHP:PROD']  # Well BHP, colon-separated
```

## Next Steps

### Immediate (same sprint)
1. **Git workflow**: Create branches, MRs for #163, #164, #165 in CLARISSA repo
2. **"Hello OPM" on Nordic VM**: Build Docker image, run SPE1 end-to-end
3. **Cloud Run deployment**: Deploy sim-engine service
4. **CI integration**: Add to `.gitlab/clarissa.yml`

### Phase A Remaining
- Integration test: submit job via API → OPM runs → parse full result
- ntfy notification on simulation completion
- Generated deck validation (parse with `opm.io.Parser`)

### Phase B (MRST + Bridge)
- **#166**: MRST Octave Backend (same SimulatorBackend pattern)
- **#170**: SimResult EvidenceProvider (Backoffice repo)
- **#167**: Delta Engine — L2-norm/NRMSE comparison
- **#171**: EventBus + Pub/Sub for sim→bridge chain

## GOV-001 Compliance
- ✅ Tests: 59 new + 31 existing = 90 sim_engine tests
- ✅ Documentation: ADR-038 current, service doc current, handover written
- ✅ Architecture: PAL pattern, clean ABC boundaries
- ✅ No direct main commits (files prepared for MR workflow)
