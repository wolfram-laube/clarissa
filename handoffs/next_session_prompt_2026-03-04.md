# Next Session Prompt — CLARISSA Sim-Engine

## Context
Sim-Engine autonomous pipeline is GREEN. OPM backend E2E passes. MRST backend has Octave OOP incompatibility (Issue #118).

## Priority Tasks

### 1. Merge MR !115 to main
Branch `refactor/117-docker-build-no-kaniko` is ready. Pipeline green, OPM E2E passing. MRST is documented known issue.

### 2. Issue #118 — MRST Octave Compatibility
The `ad-core` module uses MATLAB OOP features (`StateFunctionGrouping` property access) that Octave doesn't support. Error: `matrix cannot be indexed with .` in `checkDependencies`.

**Recommended approach:** Try MRST's `incomp` module (incompressible two-phase flow) instead of `ad-blackoil`. Simpler code path avoids the OOP issue entirely. Trade-off: simplified physics but sufficient for SPE1 validation.

Alternative: Pin an older MRST version with better Octave support, or investigate MRST patches.

### 3. Cleanup
- Remove SSH firewall rule: `gcloud compute firewall-rules delete allow-ssh-home`
- Remove dead runners from Nordic config.toml (ops-docker-runner is 403)
- Consider removing `--user` restoration in systemd unit if no issues arise

## Key References
- Cloud Run: `clarissa-sim-engine-518587440396.europe-north1.run.app`
- Nordic Shell Runner: #52090088, tags: nordic-shell, shell-any
- Pipeline trigger: `DEPLOY_SIM=true` for build+deploy, `BUILD_SIM_BASE=true` for base image
- E2E test script: See previous session transcript for `e2e_both.py`

## GOV-001 Reminder
BEFORE ANY COMMIT: create Issue → create branch → work on branch. Direct push to main = blocker.
