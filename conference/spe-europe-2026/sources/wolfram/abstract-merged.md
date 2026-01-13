# CLARISSA: A Conversational User Interface for Democratizing Reservoir Simulation

**SPE Europe Energy Conference 2026**  
**Category:** 05 Digital Transformation and Artificial Intelligence  
**Subcategory:** 05.6 Use of Machine Learning and AI in Subsurface Operations and Reservoir Optimization

---

**Authors:**  
- Douglas Perschke, Stone Ridge Technology, USA  
- Michal Matejka, Independent Consultant, Houston, USA  
- Wolfram Laube, Independent Researcher, Austria  

---

## Abstract

Reservoir simulation remains underutilized across the full spectrum of reservoir engineering—field development planning, production surveillance, forecasting, reserves booking, and exploration risking—despite decades of software advancement. The barrier is not computational; modern solvers are fast and robust. The barrier is accessibility. Graphical user interfaces (GUIs), designed to simplify simulation, have instead shifted complexity from keyword syntax to labyrinthine menus and forms. Subject matter experts bypass these interfaces entirely, writing decks directly in text editors as they have for decades. Meanwhile, practicing reservoir engineers—those who optimize producing assets, justify infill drilling, and defend reserves estimates—cannot readily access simulation because the tooling demands specialist knowledge they lack time to acquire. Even when validated models exist, they remain underutilized: engineers receive a handful of sensitivities from simulation specialists rather than fully exploring the decision space themselves. The result is over-reliance on type well profiles, analytical methods, and material balance calculations for decisions that warrant rigorous flow modeling.

This paper introduces **CLARISSA** (Conversational Language Agent for Reservoir Integrated Simulation System Analysis), which replaces the GUI paradigm with a Conversational User Interface (CUI). Rather than requiring users to navigate software, CLARISSA enables reservoir engineers to build and iterate on simulation models through natural language dialogue. The system elicits necessary inputs conversationally, translating engineering intent directly into executable simulation decks.

Recent work has demonstrated generative AI assistants that help engineers query existing models and retrieve simulator documentation (SPE-221987). CLARISSA addresses a different problem: generating complete, validated input decks from natural language specifications. Given a verbal description of a reservoir problem, CLARISSA produces a syntactically correct, physically plausible simulation deck ready for execution. The architecture combines large language models for planning and human interaction, reinforcement learning for optimizing action sequences based on numerical outcomes such as convergence behavior, and neuro-symbolic components enforcing engineering constraints and safety boundaries.

CLARISSA generates Eclipse-format decks and executes simulations using OPM Flow, enabling a web-based service model accessible to operators without commercial simulation licenses. When third-party validation is required, decks can be exported for execution on industry-standard commercial platforms. Physics-aware validation during conversational elicitation flags inconsistencies before the simulator is invoked. For incomplete specifications, the system suggests reasonable defaults informed by analog databases, explicitly documenting assumptions for engineering review.

To enable systematic evaluation of CUI-based simulation systems, we introduce **RIGOR** (Reservoir Input Generation Output Review), a benchmark framework assessing deck generation across four dimensions: syntactic validity, semantic correctness, physical plausibility, and conversational efficiency. RIGOR defines complexity tiers from foundational to advanced: a simple linear displacement model representing a laboratory coreflood, progressing through pattern floods with multi-well configurations, to mid-conversation conversion of a black-oil waterflood into a compositional equation-of-state model for tertiary recovery evaluation.

The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly.

---

## 1. Objectives and Scope

This paper introduces CLARISSA, which replaces the GUI paradigm with a Conversational User Interface (CUI) powered by large language models. Rather than requiring users to navigate software, CLARISSA enables reservoir engineers to build and iterate on simulation models through natural language dialogue. The system elicits necessary inputs conversationally, translating engineering intent directly into executable simulation decks. To enable systematic evaluation of CUI-based simulation systems, we introduce RIGOR, a benchmark framework assessing deck generation across four dimensions: syntactic validity, semantic correctness, physical plausibility, and conversational efficiency.

---

## 2. Methods, Procedures, Process

### 2.1 System Architecture

The CLARISSA architecture comprises six primary layers, each addressing distinct concerns while maintaining loose coupling through well-defined interfaces:

```mermaid
flowchart TB
    subgraph UI["User Interface Layer"]
        VOICE[Voice Input]
        TEXT[Text Chat]
        WEB[Web Interface]
        API[REST API]
    end

    subgraph TRANS["Translation Layer"]
        NLP[NL Parser]
        CONF[Confidence Scorer]
        ROLL[Rollback Manager]
    end

    subgraph CORE["CLARISSA Core"]
        LLM[LLM Layer]
        RL[RL Agent]
        NSC[Neuro-Symbolic]
    end

    subgraph VALID["Validation Layer"]
        SYN[Syntax Validator]
        SEM[Semantic Checker]
        PHY[Physics Validator]
    end

    subgraph GEN["Generation Layer"]
        DECK[Deck Generator]
        TMPL[Template Engine]
        DEF[Default Suggester]
    end

    subgraph SIM["Simulation Layer"]
        OPM[OPM Flow]
        EXP[Eclipse Export]
        RES[Result Parser]
    end

    subgraph KB["Knowledge Layer"]
        VEC[(Vector Store)]
        COR[(Corrections DB)]
        ANA[(Analog Database)]
    end

    UI --> TRANS
    TRANS --> CORE
    CORE --> VALID
    VALID --> GEN
    GEN --> SIM
    KB -.-> CORE
    SIM -.->|feedback| RL
```

**User Interface Layer:** Supports multiple interaction modalities—voice input for hands-free operation in field environments, text chat for detailed technical discussions, web interfaces for visual feedback and result exploration, and REST APIs for programmatic integration.

**Translation Layer:** Converts natural language input to valid ECLIPSE deck syntax through a multi-stage pipeline. Failed validation at any stage triggers rollback to the previous valid state. Low confidence scores prompt clarification requests rather than proceeding with uncertain interpretations.

**Core Processing Layer:** Combines LLM-based reasoning with reinforcement learning for action optimization and neuro-symbolic constraints for engineering governance.

**Validation Layer:** Multi-stage validation ensuring syntactic correctness, semantic consistency, and physical plausibility before simulation execution.

**Generation Layer:** Produces Eclipse-format decks using template engines and analog-informed defaults, with explicit documentation of all assumptions.

**Simulation Layer:** Executes via OPM Flow for open-source accessibility, with export capability for commercial platform validation.

### 2.2 Phased Development

```mermaid
flowchart LR
    subgraph P1["Phase I: Syntactic"]
        A1[Deck generation from NL]
        A2[Syntax validation]
        A3[OPM Flow integration]
    end

    subgraph P2["Phase II: Physics"]
        B1[Simulator-in-loop learning]
        B2[Convergence optimization]
        B3[Analog-based defaults]
    end

    subgraph P3["Phase III: Field"]
        C1[Embedded operational agents]
        C2[Real-time surveillance]
        C3[Multi-user collaboration]
    end

    P1 --> P2 --> P3
```

### 2.3 Comparison with Prior Work

```mermaid
flowchart LR
    subgraph ENVOY["Envoy (SPE-221987)"]
        direction TB
        E1[Query existing models]
        E2[Retrieve documentation]
        E3[RAG + Callbacks]
        E4[ECHELON<br/>Proprietary]
        E1 --> E3
        E2 --> E3
        E3 --> E4
    end

    subgraph CLARISSA["CLARISSA"]
        direction TB
        C1[Generate new decks]
        C2[Physics validation]
        C3[RL + Neuro-symbolic]
        C4[OPM Flow<br/>Open Source]
        C1 --> C3
        C2 --> C3
        C3 --> C4
    end

    ENVOY -.->|"evolution"| CLARISSA
```

| Aspect | Envoy (SPE-221987) | CLARISSA |
|--------|-------------------|----------|
| **Primary Function** | Query existing models | Generate complete decks |
| **Interaction Mode** | Q&A on loaded model | Conversational elicitation |
| **Input Modalities** | Text chat | Voice, Text, Web, API |
| **Simulator** | ECHELON (proprietary) | OPM Flow (open source) |
| **Architecture** | RAG + Callback Agents | RL + Neuro-symbolic + Feedback Loop |
| **Learning** | Static knowledge bases | Adaptive via simulation feedback |
| **Validation** | Post-hoc analysis | Pre-execution physics check |
| **Error Handling** | Manual correction | Automatic rollback + clarification |
| **Availability** | Commercial license | Web-based, license-free |

---

## 3. Results, Observations, Conclusions

### 3.1 RIGOR Benchmark Framework

```mermaid
flowchart TB
    subgraph DIMS["Evaluation Dimensions"]
        D1["Syntactic Validity"]
        D2["Semantic Correctness"]
        D3["Physical Plausibility"]
        D4["Conversational Efficiency"]
    end

    subgraph TIERS["Complexity Tiers"]
        T1["Tier 1: Foundational<br/>Linear displacement"]
        T2["Tier 2: Intermediate<br/>Pattern flood, 5-spot"]
        T3["Tier 3: Advanced<br/>Black-oil to Compositional"]
    end

    DIMS --> T1
    T1 --> T2 --> T3
```

### 3.2 Example Interaction

```mermaid
sequenceDiagram
    participant E as Field Engineer
    participant C as CLARISSA
    participant V as Validator
    participant S as OPM Flow

    Note over E: Voice input from field tablet
    E->>C: I need a waterflood model, 5-spot pattern
    C->>C: Parse intent (confidence: 0.92)
    C->>E: What is the reservoir depth and initial pressure?
    E->>C: 8500 ft TVD, about 3800 psi
    C->>V: Validate pressure gradient
    V-->>C: 0.45 psi/ft plausible
    C->>C: Generate ECLIPSE deck
    C->>E: Assumed 200 md permeability from analogs. Confirm?
    E->>C: Use 150 md, we have core data
    Note over C: Update deck, log override
    C->>S: Execute simulation
    S-->>C: Results + convergence data
    C->>E: Complete in 47s. Breakthrough at 18 months.
    E->>C: Try 20 and 80 acre spacing
    C->>C: Queue sensitivity runs
```

### 3.3 Key Capabilities Demonstrated

1. **Voice-First Field Operation:** Engineers can interact with CLARISSA from field tablets without keyboard input, enabling simulation access during well site visits.

2. **Analog-Informed Defaults:** When specifications are incomplete, CLARISSA suggests reasonable defaults from analog databases, explicitly documenting assumptions for review.

3. **Graceful Degradation:** Low-confidence interpretations trigger clarification requests rather than incorrect deck generation. Failed validations roll back to the last valid state.

4. **Mid-Conversation Model Evolution:** RIGOR Tier 3 demonstrates the ability to pivot a black-oil waterflood to a compositional EOS model for tertiary recovery—within a single conversation session.

5. **License-Free Execution:** OPM Flow integration enables operators without commercial licenses to run rigorous simulations, democratizing access to flow modeling.

---

## 4. Novelty and Contribution

The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly through:

- **Paradigm Shift:** First CUI-based system for complete simulation deck generation (vs. query-only assistants)
- **Multi-Modal Access:** Voice input enables field-based simulation workflows previously impossible
- **Open-Source Backend:** OPM Flow integration removes licensing barriers for operators
- **Systematic Benchmarking:** RIGOR provides the first standardized framework for evaluating conversational simulation systems
- **Hybrid AI Architecture:** Novel combination of LLM reasoning, reinforcement learning, and neuro-symbolic constraints for engineering-grade reliability

---

## Technical Stack

```mermaid
flowchart LR
    subgraph FE["Frontend"]
        A[Web UI - React]
        B[Voice - Whisper]
        C[API - FastAPI]
    end
    
    subgraph CORE["Core"]
        D[LLM - Claude]
        E[RL Agent - PPO]
        F[Constraints - Z3]
    end
    
    subgraph BE["Backend"]
        G[OPM Flow]
        H[Deck Generator]
        I[Vector DB]
    end

    FE --> CORE --> BE
```

---

## References

1. K. Wiegand, M. Bedewi, K. Mukundakrishnan, D. Tishechkin, V. Ananthan, and D. Kahn, "Using Generative AI to Build a Reservoir Simulation Assistant," SPE-221987-MS, ADIPEC, Abu Dhabi, 2024.

2. OPM Flow Documentation, Open Porous Media Initiative, https://opm-project.org

---

*Prepared for SPE Europe Energy Conference 2026*
