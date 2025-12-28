# ADR-004: Dual-Simulator Strategy (Superseded)

**Status:** Superseded  
**Date:** 2025-12-27  
**Superseded by:** ADR-001

## Context
Early discussions framed ORSA as a dual-simulator strategy (one production simulator + one open simulator). This simplified communication but became restrictive as the architecture expanded.

## Decision
Supersede the dual-simulator framing in favor of a physics-centric multi-simulator substrate (ADR-001).

## Consequences
- Improved extensibility and conceptual accuracy.
- Requires clearer documentation to manage complexity.
