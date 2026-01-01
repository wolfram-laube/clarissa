# ADR-010 — Project Renaming to CLARISSA

## Status
Accepted

## Context

The project previously operated under the name **ORSA (Oxy Reservoir Simulation Agent)**.
As the system evolved, the scope and nature of the artifact changed substantially:

- The system is no longer a narrow agent tied to a single operator or vendor context.
- Natural-language interaction, explanation, and reasoning have become first-class concerns.
- The architecture integrates simulation, governance, learning, and dialogue into a single coherent flow.

The name *ORSA* no longer adequately reflects:
- the conversational nature of the system,
- the integration across simulators and kernels,
- or the broader analytical role of the artifact.

A more expressive and semantically accurate project identity became necessary.

## Decision

The project is renamed to:

**CLARISSA — Conversational Language Agent for Reservoir Integrated Simulation System Analysis**

This name emphasizes:
- **Conversational** interaction as a core interface paradigm,
- **Language** as a translation layer between humans and simulation artifacts,
- **Integrated Simulation** across heterogeneous backends,
- **System Analysis** rather than narrow control or optimization.

All external-facing documentation, conceptual descriptions, and future publications
will refer to the system as **CLARISSA**.

The internal repository name and historical references may continue to mention ORSA
for traceability, but CLARISSA is the canonical project identity going forward.

## Consequences

### Positive
- Clearer conceptual framing for conferences and publications.
- Reduced coupling to vendor- or operator-specific semantics.
- Better alignment with the system’s conversational and analytical focus.

### Neutral / Transitional
- Historical artifacts (commits, branches, older ADRs) may reference ORSA.
- Some internal code symbols may still use legacy naming during transition.

### Explicitly Not Decided Here
- A full code-level rename (packages, modules) is treated as an implementation concern.
- Branding, logos, and visual identity are out of scope for this ADR.

## Related ADRs
- ADR-001 — Physics-Centric, Simulator-in-the-Loop Architecture
- ADR-002 — Separation of Reasoning, Learning, and Governance
- ADR-003 — ORSA-Native Simulation Kernel
