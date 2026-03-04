# Next Session Prompt — CLARISSA Sim-Engine 2026-03-04

## Was heute passiert ist

Issue #118 (MRST/Octave OOP Incompatibility) vollständig gelöst und deployed:
- MRST 2021a gepinnt (war 2025b) — erste offiziell Octave-verifizierte Version
- `Dockerfile.sim-base` auf GCS-Download umgestellt (pre-2024b hat keine GitHub Tags)
- GCS: `gs://myk8sproject-207017-clarissa-assets/mrst/mrst-2021a.zip` ✅
- CI komplett saniert: `build_sim_base` Shell Runner (~15min, kein Kaniko-Timeout mehr)
- `build_sim_engine`: Kaniko, GitLab Registry only
- `deploy_sim_engine`: Shell Runner, kopiert GitLab→GCP AR, dann `gcloud run deploy`
- MR !116 gemergt, Issue #118 geschlossen ✅

Issue #119 (relay.py exit code) ebenfalls gefixt:
- `relay.py --process` exitierte mit 1 wenn kein Handoff vorhanden → jetzt `sys.exit(0)`
- MR !117 gemergt, Issue #119 geschlossen ✅

Nordic Cleanup:
- config.toml: 4→2 Runner (ops-docker-runner + Duplikat entfernt)
- Stale K8s Runner #51408312 gelöscht
- SSH Firewall-Rule `allow-ssh-home` gelöscht
- `docker system prune -af` → 5.365 GB freigegeben

## Aktueller Stand

**CLARISSA Sim-Engine** läuft auf:
`clarissa-sim-engine-518587440396.europe-north1.run.app`
- MRST 2021a ✅, OPM Flow 2025.10 ✅, Octave 8.4.0 ✅
- Pipeline zuletzt grün: #2364140710

**GitLab Projekt:** `77260390`
`https://gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa`

**Nordic Runner:**
- Docker Runner: #51608579 (tag: `docker-any`)
- Shell Runner: #52090088 (tag: `nordic-shell`, `shell-any`)

## Nächste Schritte (in dieser Reihenfolge)

### 1. MR !115 mergen
War schon vor dieser Session ready — jetzt auf neuem main rebasen und mergen.
`https://gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa/-/merge_requests/115`

### 2. E2E SPE1
Erster echter Test von MRST 2021a auf Cloud Run.
Erwartung: ✅ (black-oil 3-phase, SPE1 ist in 2021a confirmed stable)

### 3. E2E SPE5
Compositional EOS — MRST Octave compat in 2021a unconfirmed.
Wenn MRST fehlschlägt: SPE5 als OPM-only in Issue #118 kommentieren und schließen.

### 4. Technical Debt (Issues anlegen)
- `docker system prune -f` als `after_script` in `build_sim_base` + `build_sim_engine`
- Scheduled weekly cleanup Job in CI
- `GOOGLE_CREDENTIALS` Phantom-Variable aus Project-CI-Vars löschen
- `SIM_GCP_IMAGE` Referenzen in `.gitlab/clarissa.yml` bereinigen

## GOV-001 GATE
**BEFORE ANY COMMIT:** Issue → Branch → Work → Commit. Kein direkter Push auf main.
