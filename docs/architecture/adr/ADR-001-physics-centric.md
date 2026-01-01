# ADR-001: Physics-Centric, Simulator-in-the-Loop Architecture

**Status:** Accepted  
**Date:** 2025-12-27

## Context
Reservoir simulation failures commonly manifest as numerical effects (non-convergence, timestep collapse, unstable solver behavior) rather than as clean logical violations. Purely text-driven or static rule-based AI assistance risks producing plausible but unsafe recommendations.

## Decision
CLARISSA treats simulators as first-class learning substrates. Simulator execution, solver diagnostics, and numerical outcomes provide primary feedback signals for learning and validation.

## Consequences
### Positive
- Learning is grounded in physical/numerical consequences.
- Architecture remains compatible with multiple simulators.
### Negative
- Requires adapter infrastructure and reproducible execution environments.
### Neutral / Open
- Specific reward shaping strategies may evolve by phase.
