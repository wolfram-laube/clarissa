# Next Session Prompt — CLARISSA Sim-Engine

## Status
Pipeline GREEN. MRST 2021a deployed auf Cloud Run. Issues #118 + #119 geschlossen.

## Sofort starten mit
1. E2E SPE1 gegen `clarissa-sim-engine-518587440396.europe-north1.run.app`
2. E2E SPE5 (compositional) — MRST Octave compat TBD, evtl. OPM-only markieren
3. MR !115 mergen (war schon vor dieser Session ready, jetzt auf neuem main)

## Dann
- Technical Debt: `docker system prune` als scheduled CI Job
- `GOOGLE_CREDENTIALS` Phantom-Variable aufräumen
- `SIM_GCP_IMAGE` Referenzen in CI bereinigen

## GOV-001 GATE
Issue → Branch → Work → Commit. Kein direkter Push auf main.
