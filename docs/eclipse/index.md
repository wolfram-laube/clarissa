# ECLIPSE Documentation

Technical documentation for ECLIPSE reservoir simulation deck syntax,
supporting CLARISSA's code generation and validation capabilities.

## Contents

| Document | Description |
|----------|-------------|
| [Deck Structure](deck-structure.md) | Section hierarchy and organization |
| [Keyword Reference](keyword-reference.md) | Alphabetical keyword listing |
| [Common Errors](common-errors.md) | Error patterns and fixes |

## Purpose

This documentation supports:

1. **CLARISSA NLP Pipeline** - Syntax generation from natural language
2. **ORSA Phase 1** - ECLIPSE debugging and code mastery
3. **Training Data** - Error pattern catalog for synthetic generation

## ECLIPSE vs OPM Flow

CLARISSA primarily targets OPM Flow, which supports most ECLIPSE 100 keywords.
This documentation covers the common subset.

| Feature | ECLIPSE | OPM Flow | CLARISSA |
|---------|---------|----------|----------|
| Black Oil | ✅ | ✅ | ✅ |
| Compositional | ✅ | Partial | 🔜 |
| Thermal | ✅ | Limited | 📋 |
| Polymer/Surfactant | ✅ | Partial | 📋 |

## Related Resources

- [OPM Flow Guide](../simulators/opm-flow.md) - Simulator integration
- [Adapter Contract](../simulators/adapter-contract.md) - Validation interface
- ADR-009 - NLP Translation Pipeline
- ORSA Proposal - Phase 1 Code Mastery objectives