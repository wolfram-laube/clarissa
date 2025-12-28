# ADR-003: ORSA-Native Simulation Kernel

**Status:** Accepted  
**Date:** 2025-12-27

## Context
Production simulators provide operational fidelity but limited introspection and controlled experimentation. ORSA needs a fully observable environment for explanation, sensitivity analysis, and learning-signal generation.

## Decision
Introduce a lightweight ORSA-native simulation kernel (laboratory environment) that complements production simulators. It is not a replacement for production simulators.

## Consequences
### Positive
- Enables controlled experiments and explainability.
- Supports learning signal generation and future differentiability.
### Negative
- Adds maintenance burden for a custom numerical core.
### Neutral / Open
- Kernel scope will expand incrementally by phase.
