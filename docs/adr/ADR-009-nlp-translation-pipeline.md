# ADR-009: Multi-Stage NLP Translation Pipeline

**Status:** Proposed  
**Date:** 2025-12-29  
**Related:** ADR-001, ADR-002, ADR-003

---

## Context

CLARISSA's core value proposition is translating natural language (voice or text) into valid, physics-consistent reservoir simulation syntax. This translation is non-trivial:

- Reservoir simulation languages (ECLIPSE, OPM) have complex, interdependent keyword structures.
- Ambiguous or incomplete user input must be resolved against asset-specific context.
- Generated syntax must satisfy both syntactic validity and physical consistency.
- Confidence must be quantified; low-confidence interpretations should trigger clarification rather than silent errors.

A monolithic end-to-end model (speech → ECLIPSE) would be opaque, difficult to debug, and impossible to validate incrementally. Errors could propagate silently, producing syntactically valid but physically nonsensical decks.

## Decision

CLARISSA implements a **multi-stage translation pipeline** with explicit validation checkpoints between stages:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Speech    │───▶│   Intent    │───▶│   Entity    │
│ Recognition │    │ Recognition │    │ Extraction  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
   [Validate]        [Validate]        [Validate]
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Asset    │───▶│   Syntax    │───▶│    Deck     │
│ Validation  │    │ Generation  │    │ Validation  │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Stage Responsibilities

| Stage | Input | Output | Validation |
|-------|-------|--------|------------|
| Speech Recognition | Audio stream | Text transcription | Confidence ≥ threshold |
| Intent Recognition | Text | Intent class + confidence | Known intent, confidence ≥ threshold |
| Entity Extraction | Text + Intent | Structured entities (wells, rates, dates) | All required entities present |
| Asset Validation | Entities | Validated entities | Entities exist in asset database |
| Syntax Generation | Validated entities + Intent | ECLIPSE keyword sequence | Syntactic validity |
| Deck Validation | Generated syntax | Validated deck | Physics consistency |

### Failure Handling

Each validation checkpoint follows the same pattern:

1. **High confidence, valid:** Proceed to next stage.
2. **Low confidence:** Request clarification from user; do not proceed.
3. **Invalid:** Roll back to previous valid state; explain failure.

No stage may "skip" validation or proceed with uncertain results.

### Model Abstraction

Each stage that involves ML inference uses the model abstraction layer (per ADR-002):

- Stages are not tied to specific model implementations.
- Local models (CodeLlama, Whisper) for air-gapped deployments.
- External APIs (Claude, GPT) for connected environments.
- Custom fine-tuned models for specialized deployments.

Selection is configuration-driven, not code-driven.

## Rationale

### Why Multi-Stage?

- **Debuggability:** Failures localize to specific stages.
- **Testability:** Each stage can be tested independently with contract tests.
- **Explainability:** Pipeline state is inspectable at each checkpoint.
- **Graceful degradation:** Partial results are possible (e.g., intent recognized but entities ambiguous).

### Why Explicit Validation?

- Reservoir simulation errors can be costly (bad forecasts, incorrect decisions).
- Silent failures are unacceptable in engineering domains.
- Validation checkpoints enforce the principle: "When uncertain, ask; don't guess."

### Alignment with Other ADRs

- **ADR-001 (Physics-Centric):** Deck Validation stage uses simulator feedback for physics consistency.
- **ADR-002 (Separation of Roles):** NLP pipeline is separate from RL learning and Governance enforcement.
- **ADR-003 (Native Kernel):** Kernel may provide fast physics pre-checks before full simulation.

## Consequences

### Positive

- Clear, auditable translation process.
- Failures are localized and explainable.
- Confidence thresholds prevent silent errors.
- Stages can evolve independently (e.g., swap ASR provider without touching syntax generation).

### Negative

- More components to maintain than a monolithic approach.
- Latency increases with each stage (mitigated by parallelization where possible).
- Requires careful interface contracts between stages.

### Neutral / Open

- Specific model choices per stage will be determined by experimentation.
- Confidence thresholds may require tuning per deployment.
- Caching strategies for repeated queries are not yet defined.

## Implementation Notes

- Each stage SHOULD expose a Protocol (interface) for testability.
- Validation checkpoints SHOULD emit structured logs for observability.
- The pipeline controller SHOULD be stateless; state lives in the request context.
- Initial implementation MAY stub expensive stages (ASR, Syntax Generation) with mocks.

## Alternatives Considered

### End-to-End Model

A single model trained on (speech, ECLIPSE deck) pairs.

- **Rejected:** Opaque, difficult to debug, no intermediate validation.

### Two-Stage (Intent → Deck)

Skip entity extraction; generate deck directly from intent.

- **Rejected:** Insufficient granularity for validation and error localization.

### Rule-Based Translation

Template-based generation without ML.

- **Rejected:** Cannot handle natural language variability; too brittle.

## Cross-References

- ADR-001 — Physics-Centric, Simulator-in-the-Loop Architecture
- ADR-002 — Separation of Reasoning, Learning, and Governance
- ADR-003 — CLARISSA-Native Simulation Kernel
- ADR-007 — CI as an Observability Layer
- IJACSA Paper — Section III.C (NLP Translation Layer)
