# NEXT SESSION — CLARISSA Sim-Engine Phase A Deployment

## Context
Phase A code is complete: deck_generator.py (#164), opm_backend.py (#163),
sim_api.py (#165) + Dockerfile. All 59 tests pass, SPE1 reference data
validates correctly. Code is in working directory — needs Git workflow.

### ERLEDIGT (Session 22.02.2026):
- #164 deck_generator.py — SimRequest → Eclipse .DATA (250 LOC, 16 tests)
- #163 opm_backend.py — OPMBackend(SimulatorBackend) with opm.io parsing (350 LOC, 18 tests)
- #165 sim_api.py — FastAPI with async job queue + Dockerfile (200 LOC, 4 tests)
- SPE1 reference validation: FOPR, WBHP, PRESSURE, SGAS all match ✅
- 59 new tests (test_sim_engine_phase_a.py), 322 total CLARISSA tests

### Key Discovery: OPM Python Import Paths
```python
from opm.io.ecl import ERst, ESmry, EGrid  # Correct!
# NOT from opm.io directly (those classes aren't re-exported)
```

## NÄCHSTE SCHRITTE:

### 1. Git Workflow (MRs in CLARISSA Repo)
```bash
# Create branch from main
git checkout -b feature/163-opm-flow-backend
# Add the new files:
# - src/clarissa/sim_engine/deck_generator.py
# - src/clarissa/sim_engine/backends/opm_backend.py
# - src/clarissa/sim_engine/sim_api.py
# - src/clarissa/sim_engine/Dockerfile
# - tests/test_sim_engine_phase_a.py
# - Updated __init__.py
# Create MR → merge
```

### 2. "Hello OPM" on Nordic VM
```bash
# SSH into Nordic VM
cd ~/clarissa
docker build -t clarissa-sim -f src/clarissa/sim_engine/Dockerfile .
docker run -p 8080:8080 clarissa-sim
# Test: curl http://localhost:8080/health
# Submit SPE1: curl -X POST http://localhost:8080/sim/run -d '...'
```

### 3. Cloud Run Deployment
- Use same pattern as dialectic-api deployment
- Service name: clarissa-sim-engine
- Region: europe-west1
- Memory: 8GB (for OPM Flow)

### 4. CI Integration
Add to `.gitlab/clarissa.yml`:
- Test job: runs test_sim_engine_phase_a.py
- Docker build job: builds sim-engine image
- Deploy job: pushes to Cloud Run

### 5. Phase B Prep
- #166 MRST Octave Backend
- #170 SimResult EvidenceProvider (Backoffice repo)

## Files Location
All new files are in the CLARISSA repo working copy.
Handover: docs/handover/HANDOVER_CLARISSA_SIM_PHASE_A_22_02_2026.md
