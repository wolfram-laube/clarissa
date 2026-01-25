# CLARISSA Project Context

## Overview

**CLARISSA** (Conversational Language Agent for Reservoir Integrated Simulation System Analysis) ist ein NLP-System das natürliche Sprache in Reservoir-Simulator-Befehle übersetzt.

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                     NLP Pipeline (ADR-009)                  │
├─────────────────────────────────────────────────────────────┤
│  1. Speech Recognition (optional)                           │
│  2. Intent Recognition    → 22 Intents, 6 Kategorien       │
│  3. Entity Extraction     → 8 Entity-Typen                 │
│  4. Asset Validation      → Gegen Modell-Inventory         │
│  5. Syntax Generation     → ECLIPSE/OPM Keywords           │
│  6. Deck Validation       → Simulator-Feedback             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Simulator Backend                         │
│  • OPM Flow (Docker)    - Primary, open-source              │
│  • MockSimulator        - Testing                           │
│  • ECLIPSE (future)     - Commercial                        │
└─────────────────────────────────────────────────────────────┘
```

## Intent-Kategorien (aktuell 22)

| Kategorie | Intents |
|-----------|---------|
| `simulation_control` | RUN_SIMULATION, STOP_SIMULATION, RESTART_SIMULATION |
| `well_operations` | ADD_WELL, MODIFY_WELL, SHUT_WELL, OPEN_WELL, SET_RATE, SET_PRESSURE |
| `schedule_operations` | SET_DATE, ADD_TIMESTEP, MODIFY_SCHEDULE |
| `query_operations` | GET_PRODUCTION, GET_PRESSURE, GET_SATURATION, GET_WELLS, GET_SCHEDULE |
| `validation` | VALIDATE_DECK, CHECK_CONVERGENCE, VALIDATE_PHYSICS |
| `help_and_info` | GET_HELP, EXPLAIN_KEYWORD, LIST_KEYWORDS |

## Entity-Typen (aktuell 8)

| Entity | Beispiel | Pattern |
|--------|----------|---------|
| `well_name` | PROD-01, INJ_A | Alphanumerisch + Bindestrich |
| `rate_value` + `rate_unit` | 500 bbl/day | Zahl + Einheit |
| `pressure_value` + `pressure_unit` | 2000 psi | Zahl + Einheit |
| `target_date` | 2025-06-15, January 2026 | ISO oder Monat+Jahr |
| `timestep_size` + `timestep_unit` | 30 days | Zahl + Zeiteinheit |
| `phase` | oil, water, gas | Keyword |
| `well_type` | producer, injector | Keyword |
| `grid_location` | I=10 J=15 | Grid-Koordinaten |

## Validation Checkpoint (3-State)

Zwischen jeder Pipeline-Stage:
1. **PROCEED** - Confidence ≥ 80%, keine Errors → weiter
2. **CLARIFY** - Confidence 50-80% → User fragen
3. **ROLLBACK** - Confidence < 50% oder Errors → zurück

## Key Architecture Decisions (ADRs)

- **ADR-001:** Physics-Centric, Simulator-in-the-Loop
- **ADR-004:** Dual Simulator Strategy (OPM + Mock)
- **ADR-009:** Multi-Stage NLP Translation Pipeline
- **ADR-011:** OPM Flow Integration
- **ADR-012:** Container Registry & K8s Strategy

## Repository

- **GitLab:** https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa
- **Docs:** https://wolfram_laube.gitlab.io/blauweiss_llc/clarissa/

## Tech Stack

- Python 3.11+
- pytest, ruff
- Docker (OPM Flow)
- GitLab CI/CD
- MkDocs (Dokumentation)
