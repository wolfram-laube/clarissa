# ADR-002: Separation of Reasoning, Learning, and Governance

**Status:** Accepted  
**Date:** 2025-12-27

## Context
In safety-critical engineering domains, a single AI paradigm should not combine reasoning, learning, and decision authority. Mixing these responsibilities reduces auditability and increases risk.

## Decision
CLARISSA separates:
- LLM reasoning & interaction (planning, explanation, translation),
- Reinforcement learning (skill acquisition for action sequences),
- Neuro-symbolic governance (rules, constraints, escalation, approvals).

## Consequences
### Positive
- Clear bounded autonomy and traceability.
- Governance can be audited independently from learning.
### Negative
- More components and interfaces to maintain.
### Neutral / Open
- Specific governance policies will mature via additional ADRs.
