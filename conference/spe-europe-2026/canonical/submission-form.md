# SPE Meeting Abstract Submission

**Meeting Category:** 05 Digital Transformation and Artificial Intelligence  
**Subcategory:** 05.6 Use of Machine Learning and AI in Subsurface Operations and Reservoir Optimization

**TITLE:** CLARISSA: A Conversational User Interface for Democratizing Reservoir Simulation

**Authors:** Wolfram Laube¹, Douglas Perschke², Mike [TBD]³  
¹Independent Researcher, Austria | ²[Affiliation TBD] | ³[Affiliation TBD]

---

## 1. Objectives/Scope (25-75 words)

This paper introduces CLARISSA (Conversational Language Agent for Reservoir Integrated Simulation System Analysis), which replaces the GUI paradigm with a Conversational User Interface (CUI). Rather than requiring users to navigate software, CLARISSA enables reservoir engineers to build and iterate on simulation models through natural language dialogue—including voice input for field operations. The system elicits necessary inputs conversationally, translating engineering intent directly into executable simulation decks. To enable systematic evaluation, we introduce RIGOR (Reservoir Input Generation Output Review), a benchmark framework assessing deck generation across syntactic validity, semantic correctness, physical plausibility, and conversational efficiency.

**Word count: 89**

---

## 2. Methods, Procedures, Process (75-100 words)

CLARISSA combines large language models for natural language understanding, reinforcement learning for optimizing action sequences based on simulation outcomes, and neuro-symbolic components enforcing engineering constraints. The six-layer architecture supports multiple interaction modalities: voice input for hands-free field operation, text chat for technical discussions, web interfaces for visual feedback, and REST APIs for programmatic integration. The translation layer converts natural language to valid ECLIPSE deck syntax through a multi-stage validation pipeline. Failed validation triggers rollback to the previous valid state; low confidence scores prompt clarification requests rather than proceeding with uncertain interpretations. CLARISSA executes simulations via OPM Flow, enabling license-free web-based access.

**Word count: 101**

---

## 3. Results, Observations, Conclusions (100-200 words)

Recent work has demonstrated generative AI assistants that help engineers query existing models and retrieve simulator documentation (SPE-221987). CLARISSA addresses a different problem: generating complete, validated input decks from natural language specifications. Given a verbal description of a reservoir problem, CLARISSA produces a syntactically correct, physically plausible simulation deck ready for execution.

The system incorporates physics-aware validation during elicitation, flagging inconsistencies before the simulator is invoked. For incomplete specifications, CLARISSA suggests reasonable defaults informed by analog databases, explicitly documenting assumptions for engineering review. When third-party validation is required, Eclipse-format decks can be exported for execution on industry-standard commercial platforms.

The RIGOR benchmark framework defines complexity tiers from foundational to advanced: a simple linear displacement model representing a laboratory coreflood, progressing through pattern floods with multi-well configurations, to mid-conversation conversion of a black-oil waterflood into a compositional equation-of-state model for tertiary recovery evaluation.

CLARISSA evolves through three development phases: syntactic assistance (current), physics-informed support with simulator-in-loop learning, and ultimately field-specialized agents embedded in operational teams.

**Word count: 178**

---

## 4. Novelty and Additive Information (25-75 words)

Reservoir simulation remains underutilized despite decades of software advancement. The barrier is not computational—modern solvers are fast and robust. The barrier is accessibility. GUIs have shifted complexity from keyword syntax to labyrinthine menus. Practicing reservoir engineers cannot readily access simulation because tooling demands specialist knowledge they lack time to acquire. The result is over-reliance on type well profiles and analytical methods for decisions that warrant rigorous flow modeling. The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly through voice-enabled conversational interaction and license-free execution via OPM Flow.

**Word count: 103**

---

## Key Differentiators from Prior Work (SPE-221987)

| Aspect | Envoy (SPE-221987) | CLARISSA |
|--------|-------------------|----------|
| Primary Function | Query existing models | Generate complete decks |
| Interaction Mode | Text Q&A on loaded model | Voice + Text elicitation |
| Simulator | ECHELON (proprietary) | OPM Flow (open source) |
| Architecture | RAG + Callback Agents | RL + Neuro-symbolic + Feedback Loop |
| Learning | Static knowledge bases | Adaptive via simulation feedback |
| Validation | Post-hoc analysis | Pre-execution physics check with rollback |
| Availability | Commercial license | Web-based, license-free |

---

## Figures (for full paper)

1. **System Architecture** - Six-layer design with loose coupling
2. **Development Phases** - Timeline from Phase I (Syntactic) through Phase III (Field-Specialized)
3. **Envoy vs CLARISSA** - Evolution from query-based to generation-based paradigm
4. **RIGOR Framework** - Four evaluation dimensions across three complexity tiers
5. **Conversation Flow** - Example voice interaction from field tablet
6. **Technical Stack** - Frontend, Core, Backend components

---

*Submitted to SPE Europe Energy Conference 2026*
