#set document(
  title: "CLARISSA: A Conversational User Interface for Democratizing Reservoir Simulation",
  author: ("Wolfram Laube", "Douglas Perschke", "Mike [TBD]"),
)

#set page(paper: "a4", margin: 2.5cm)
#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true, leading: 0.65em)
#set heading(numbering: "1.")

#let spe-blue = rgb("#003366")
#let accent = rgb("#0066cc")

#align(center)[
  #block(fill: spe-blue, inset: 8pt, radius: 4pt)[
    #text(fill: white, weight: "bold", size: 0.9em)[SPE Europe Energy Conference 2026]
  ]
  
  #v(0.3em)
  #text(fill: accent, size: 0.9em)[
    05 Digital Transformation and AI → 05.6 ML/AI in Subsurface Operations
  ]
  
  #v(0.8em)
  
  #text(size: 1.6em, weight: "bold", fill: spe-blue)[
    #smallcaps[CLARISSA]: A Conversational User Interface for Democratizing Reservoir Simulation
  ]
  
  #v(1em)
  
  #text(weight: "bold")[Wolfram Laube]#super[1], 
  #text(weight: "bold")[Douglas Perschke]#super[2], 
  #text(weight: "bold")[Mike \[TBD\]]#super[3]
  
  #v(0.3em)
  #text(size: 0.9em, style: "italic")[
    #super[1]Independent Researcher, Austria | 
    #super[2]\[Affiliation TBD\] | 
    #super[3]\[Affiliation TBD\]
  ]
]

#v(1em)

#block(fill: rgb("#e8f0f8"), inset: 12pt, radius: 4pt, stroke: (left: 4pt + spe-blue))[
  #heading(level: 1, numbering: none)[Abstract]
  
  Reservoir simulation remains underutilized across the full spectrum of reservoir engineering—field development planning, production surveillance, forecasting, reserves booking, and exploration risking—despite decades of software advancement. The barrier is not computational; modern solvers are fast and robust. *The barrier is accessibility.*

  This paper introduces *#smallcaps[CLARISSA]* (Conversational Language Agent for Reservoir Integrated Simulation System Analysis), which replaces the GUI paradigm with a Conversational User Interface (CUI). Rather than requiring users to navigate software, CLARISSA enables reservoir engineers to build and iterate on simulation models through natural language dialogue—including _voice input for hands-free field operations_.

  Recent work has demonstrated generative AI assistants that help engineers query existing models (SPE-221987). CLARISSA addresses a different problem: *generating complete, validated input decks from natural language specifications*. The architecture combines large language models, reinforcement learning for action optimization, and neuro-symbolic components enforcing engineering constraints.

  CLARISSA executes simulations via OPM Flow, enabling license-free web-based access. To enable systematic evaluation, we introduce *#smallcaps[RIGOR]* (Reservoir Input Generation Output Review), a benchmark spanning coreflood models to mid-conversation compositional EOS pivots.

  _The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly._
]

#v(0.5em)
#block(fill: rgb("#f5f5f5"), inset: 10pt, radius: 4pt)[
  *Keywords:* Reservoir Simulation, Conversational UI, Voice Interface, Generative AI, LLM, OPM Flow, Deck Generation, Reinforcement Learning, Neuro-symbolic AI
]

= System Architecture

The CLARISSA architecture comprises six primary layers, each addressing distinct concerns while maintaining loose coupling through well-defined interfaces.

#figure(
  image("diagrams/architecture-6layer.svg", width: 95%),
  caption: [CLARISSA Six-Layer Architecture: User Interface (Voice, Text, Web, API), Translation, Core Processing (LLM, RL, Neuro-symbolic), Validation, Generation, and Simulation layers.],
) <fig-arch>

#grid(columns: 2, gutter: 1em,
  block(fill: rgb("#fff"), inset: 10pt, radius: 4pt, stroke: 1pt + rgb("#ddd"))[
    *🎤 Voice-First Design* \
    #text(size: 0.9em)[Hands-free operation from field tablets during well site visits]
  ],
  block(fill: rgb("#fff"), inset: 10pt, radius: 4pt, stroke: 1pt + rgb("#ddd"))[
    *🔄 Graceful Degradation* \
    #text(size: 0.9em)[Low confidence triggers clarification; failures roll back]
  ],
  block(fill: rgb("#fff"), inset: 10pt, radius: 4pt, stroke: 1pt + rgb("#ddd"))[
    *📊 Analog-Informed Defaults* \
    #text(size: 0.9em)[Missing parameters from basin-specific databases]
  ],
  block(fill: rgb("#fff"), inset: 10pt, radius: 4pt, stroke: 1pt + rgb("#ddd"))[
    *🆓 License-Free Execution* \
    #text(size: 0.9em)[OPM Flow enables operators without commercial licenses]
  ],
)

= Development Phases

#figure(
  image("diagrams/phases.svg", width: 85%),
  caption: [CLARISSA Development Roadmap: Phase I (Syntactic), Phase II (Physics-Informed), Phase III (Field-Specialized).],
) <fig-phases>

= Comparison with Prior Work

#figure(
  image("diagrams/comparison.svg", width: 80%),
  caption: [Evolution from Envoy (SPE-221987) to CLARISSA: Query-based vs. Generation-based paradigm.],
) <fig-comparison>

#figure(
  table(
    columns: 3,
    stroke: none,
    align: (left, left, left),
    table.hline(),
    table.header([*Aspect*], [*Envoy (SPE-221987)*], [*CLARISSA*]),
    table.hline(),
    [Primary Function], [Query existing models], [Generate complete decks],
    [Interaction Mode], [Text Q&A on loaded model], [Voice + Text elicitation],
    [Input Modalities], [Text chat only], [Voice, Text, Web, API],
    [Simulator], [ECHELON (proprietary)], [OPM Flow (open source)],
    [Architecture], [RAG + Callback Agents], [RL + Neuro-symbolic + Feedback],
    [Learning], [Static knowledge bases], [Adaptive via sim feedback],
    [Error Handling], [Manual correction], [Auto rollback + clarification],
    [Validation], [Post-hoc analysis], [Pre-execution physics check],
    [Availability], [Commercial license], [Web-based, license-free],
    table.hline(),
  ),
  caption: [Feature Comparison: Envoy vs. CLARISSA],
) <tab-comparison>

= RIGOR Benchmark Framework

#figure(
  image("diagrams/rigor.svg", width: 75%),
  caption: [RIGOR Framework: Four evaluation dimensions across three complexity tiers.],
) <fig-rigor>

*Evaluation Dimensions:*
+ *Syntactic Validity:* Parser acceptance, keyword correctness
+ *Semantic Correctness:* Logical consistency, unit coherence  
+ *Physical Plausibility:* Pressure gradients, saturations, rates within bounds
+ *Conversational Efficiency:* Turns to completion, clarification rate

*Complexity Tiers:*
- *Tier 1 (Foundational):* Linear displacement / laboratory coreflood
- *Tier 2 (Intermediate):* Pattern flood, 5-spot, 40-acre spacing
- *Tier 3 (Advanced):* Mid-conversation black-oil → compositional EOS pivot

= Example Interaction

#figure(
  image("diagrams/conversation.svg", width: 95%),
  caption: [Voice-based field interaction sequence with physics validation and sensitivity analysis.],
) <fig-conversation>

= Conclusions

CLARISSA represents a paradigm shift in reservoir simulation accessibility:

- *First CUI-based system* for complete simulation deck generation
- *Voice-enabled field workflows* previously impossible
- *License-free execution* via OPM Flow removes barriers
- *RIGOR benchmark* provides first standardized evaluation framework
- *Hybrid AI architecture* combines LLM, RL, and neuro-symbolic components

_The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. CLARISSA addresses that constraint directly._

#heading(level: 1, numbering: none)[References]

1. K. Wiegand et al., "Using Generative AI to Build a Reservoir Simulation Assistant," SPE-221987-MS, ADIPEC 2024.

2. Open Porous Media Initiative, "OPM Flow Documentation," https://opm-project.org
