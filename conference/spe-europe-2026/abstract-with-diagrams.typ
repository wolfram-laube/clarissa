#set document(
  title: "CLARISSA: A Conversational Agent Architecture for Democratizing Reservoir Simulation",
  author: "Wolfram Laube",
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
)

#set text(
  font: "New Computer Modern",
  size: 11pt,
)

#set par(
  justify: true,
  leading: 0.65em,
)

#set heading(numbering: "1.")

#let spe-blue = rgb("#003366")

#align(center)[
  #text(size: 0.9em, fill: spe-blue, weight: "bold")[
    SPE Europe Energy Conference 2026
  ]
  
  #v(0.5em)
  
  #text(size: 1.5em, weight: "bold", fill: spe-blue)[
    #smallcaps[CLARISSA]: A Conversational Agent Architecture for Democratizing Reservoir Simulation
  ]
  
  #v(0.3em)
  
  #text(style: "italic")[
    Technical Category: Digitalization / Reservoir Simulation
  ]
  
  #v(0.8em)
  
  #text(weight: "bold")[Wolfram Laube] \
  #text(style: "italic")[Independent Researcher, Austria]
]

#v(1em)

#heading(level: 1, numbering: none)[Abstract]

Reservoir simulation remains underutilized across the full spectrum of reservoir engineering—field development planning, production surveillance, forecasting, reserves booking, and exploration risking—despite decades of software advancement. The barrier is not computational; modern solvers are fast and robust. The barrier is accessibility. Graphical user interfaces, designed to simplify simulation, have shifted complexity from keyword syntax to labyrinthine menus.

This paper introduces *#smallcaps[CLARISSA]* (Conversational Language Agent for Reservoir Integrated Simulation System Analysis), a phased AI agent architecture that replaces the GUI paradigm with physics-aware conversational interaction. Rather than requiring users to navigate software, CLARISSA enables reservoir engineers to build and iterate on simulation models through natural language dialogue.

Recent work has demonstrated generative AI assistants that help engineers query existing models and retrieve simulator documentation (SPE-221987). CLARISSA addresses a different problem: generating complete, validated input decks from natural language specifications while maintaining simulator-in-the-loop feedback for physics-grounded reasoning. The architecture combines large language models for planning and human interaction, reinforcement learning for optimizing action sequences based on numerical outcomes such as convergence behavior, and neuro-symbolic components enforcing engineering constraints and safety boundaries.

CLARISSA integrates OPM Flow as primary execution backend, enabling a web-based service model accessible to operators without commercial simulation licenses. To enable systematic evaluation, we introduce *#smallcaps[RIGOR]* (Reservoir Input Generation Output Review), a benchmark framework assessing deck generation across four dimensions: syntactic validity, semantic correctness, physical plausibility, and conversational efficiency.

_The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly._

#v(0.5em)

#block(
  fill: rgb("#e8f0f8"),
  inset: 10pt,
  radius: 2pt,
)[
  *Keywords:* Reservoir Simulation, Generative AI, Large Language Models, Natural Language Processing, OPM Flow, Conversational Agents, Deck Generation
]

#pagebreak()

= Architecture Overview

The CLARISSA system architecture comprises four primary layers: User Interface, Core Processing, Simulation, and Knowledge Management.

#figure(
  image("diagrams/architecture.svg", width: 90%),
  caption: [CLARISSA System Architecture showing the interaction between User Interface, Core (LLM, RL Agent, Neuro-Symbolic Constraints), Simulation (Validator, Generator, OPM Flow), and Knowledge layers.],
) <fig-architecture>

= Development Phases

CLARISSA evolves through three phases: syntactic assistance for deck generation and debugging, physics-informed support incorporating simulation feedback loops, and ultimately field-specialized agents embedded in operational teams.

#figure(
  image("diagrams/phases.svg", width: 85%),
  caption: [CLARISSA Development Phases: Phase I (Syntactic Assistance), Phase II (Physics-Informed), and Phase III (Field-Specialized).],
) <fig-phases>

= Comparison with Prior Work

@fig-comparison and @tab-comparison illustrate the key differences between CLARISSA and the Envoy system described in SPE-221987.

#figure(
  image("diagrams/comparison.svg", width: 80%),
  caption: [Evolution from Envoy (SPE-221987) to CLARISSA: Query-based vs. Generation-based approaches.],
) <fig-comparison>

#figure(
  table(
    columns: 3,
    stroke: none,
    align: (left, left, left),
    table.hline(),
    table.header(
      [*Aspect*], [*Envoy (SPE-221987)*], [*CLARISSA*],
    ),
    table.hline(),
    [Primary Function], [Query existing models], [Generate complete decks],
    [Interaction Mode], [Q&A on loaded model], [Elicitation dialogue],
    [Simulator], [ECHELON (proprietary)], [OPM Flow (open source)],
    [Architecture], [RAG + Callback Agents], [RL + Neuro-symbolic + Loop],
    [Learning], [Static knowledge bases], [Adaptive via sim feedback],
    [Availability], [Commercial license], [Web-based, license-free],
    [Validation], [Post-hoc analysis], [Pre-execution physics check],
    table.hline(),
  ),
  caption: [Feature Comparison: Envoy vs. CLARISSA],
) <tab-comparison>

= RIGOR Benchmark Framework

To enable systematic evaluation, we introduce RIGOR (Reservoir Input Generation Output Review).

#figure(
  image("diagrams/rigor.svg", width: 75%),
  caption: [RIGOR Benchmark Framework: Four evaluation dimensions applied across three complexity tiers.],
) <fig-rigor>

= Conversation Flow

@fig-conversation demonstrates a typical interaction sequence between an engineer and CLARISSA.

#figure(
  image("diagrams/conversation.svg", width: 95%),
  caption: [Example conversation flow showing iterative model specification, validation, and simulation execution.],
) <fig-conversation>

= Technical Stack

#figure(
  image("diagrams/techstack.svg", width: 70%),
  caption: [CLARISSA Technical Stack: Frontend, Core, and Simulation components.],
) <fig-techstack>

= Conclusions

CLARISSA represents a fundamental shift in how reservoir engineers can interact with simulation tools. By replacing the GUI paradigm with physics-aware conversational interaction, we address the accessibility barrier that has limited simulation adoption across the industry.

#heading(level: 1, numbering: none)[References]

K. Wiegand, M. Bedewi, K. Mukundakrishnan, D. Tishechkin, V. Ananthan, and D. Kahn, "Using Generative AI to Build a Reservoir Simulation Assistant," SPE-221987-MS, ADIPEC, Abu Dhabi, 2024.
