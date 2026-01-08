// CLARISSA SPE Europe 2026 Abstract
// Typst version

#set document(
  title: "CLARISSA: A Conversational Agent Architecture for Democratizing Reservoir Simulation",
  author: ("Wolfram Laube", "Mike [Surname]"),
  date: datetime.today(),
)

#set page(
  paper: "a4",
  margin: 2.5cm,
  header: align(right, text(size: 9pt, fill: gray)[SPE Europe Energy Conference 2026]),
  footer: align(center, text(size: 9pt, fill: gray)[Page #counter(page).display()]),
)

#set text(
  font: "New Computer Modern",
  size: 11pt,
)

#set par(
  justify: true,
  leading: 0.65em,
)

#let clarissa = smallcaps[Clarissa]
#let rigor = smallcaps[Rigor]
#let spe-blue = rgb("#003366")

// Title
#align(center)[
  #block(text(size: 16pt, weight: "bold", fill: spe-blue)[
    CLARISSA: A Conversational Agent Architecture\ for Democratizing Reservoir Simulation
  ])
  
  #v(0.5em)
  
  #text(size: 12pt)[
    Wolfram Laube#super[1] and Mike \[Surname\]#super[2]
  ]
  
  #v(0.3em)
  
  #text(size: 10pt, fill: gray)[
    #super[1]Independent Researcher, Austria \
    #super[2]\[Affiliation\]
  ]
  
  #v(0.3em)
  
  #text(size: 10pt, fill: gray)[
    Technical Category: Digitalization / Reservoir Simulation
  ]
]

#v(1em)

// Abstract
#block(
  width: 100%,
  inset: (left: 0.5cm, right: 0.5cm),
)[
  #text(weight: "bold")[Abstract]
  
  Reservoir simulation remains underutilized across the full spectrum of reservoir engineering—field development planning, production surveillance, forecasting, reserves booking, and exploration risking—despite decades of software advancement. The barrier is not computational; modern solvers are fast and robust. The barrier is accessibility. Graphical user interfaces, designed to simplify simulation, have shifted complexity from keyword syntax to labyrinthine menus. Subject matter experts bypass these interfaces entirely, writing decks in text editors as they have for decades. Meanwhile, practicing reservoir engineers—those who optimize producing assets, justify infill drilling, and defend reserves estimates—cannot readily access simulation because the tooling demands specialist knowledge they lack time to acquire. Even when validated models exist, they remain underutilized: engineers receive a handful of sensitivities from simulation specialists rather than exploring the decision space themselves.

  This paper introduces #clarissa (Conversational Language Agent for Reservoir Integrated Simulation System Analysis), a phased AI agent architecture that replaces the GUI paradigm with physics-aware conversational interaction. Rather than requiring users to navigate software, #clarissa enables reservoir engineers to build and iterate on simulation models through natural language dialogue.

  Recent work has demonstrated generative AI assistants that help engineers query existing models and retrieve simulator documentation (SPE-221987). #clarissa addresses a different problem: generating complete, validated input decks from natural language specifications while maintaining simulator-in-the-loop feedback for physics-grounded reasoning. The architecture combines large language models for planning and human interaction, reinforcement learning for optimizing action sequences based on numerical outcomes such as convergence behavior, and neuro-symbolic components enforcing engineering constraints and safety boundaries.

  #clarissa integrates OPM Flow as primary execution backend, enabling a web-based service model accessible to operators without commercial simulation licenses. When third-party validation is required, Eclipse-format decks can be exported for execution on industry-standard platforms. Physics-aware validation during conversational elicitation flags inconsistencies before simulation; for incomplete specifications, the system suggests defaults informed by analog databases, explicitly documenting assumptions for engineering review.

  To enable systematic evaluation, we introduce #rigor (Reservoir Input Generation Output Review), a benchmark framework assessing deck generation across four dimensions: syntactic validity, semantic correctness, physical plausibility, and conversational efficiency. #rigor defines complexity tiers from foundational single-well models through pattern floods to multi-phase compositional scenarios.

  #clarissa evolves through three phases: syntactic assistance for deck generation and debugging, physics-informed support incorporating simulation feedback loops, and ultimately field-specialized agents embedded in operational teams. This paper presents the architectural foundations and Phase I implementation targeting syntactic deck generation with validation.

  The binding constraint on simulation adoption has never been solver performance. It is human cognitive load and workflow friction. #clarissa addresses that constraint directly.
]

#v(0.5em)
*Keywords:* Reservoir Simulation, Generative AI, Conversational Interface, Natural Language Processing, OPM Flow, Automation

#v(1.5em)

// Comparison Table
#text(size: 12pt, weight: "bold")[Key Differentiators from Prior Work]

#v(0.5em)

#table(
  columns: (1fr, 1.5fr, 1.5fr),
  align: (left, left, left),
  stroke: none,
  inset: 6pt,
  
  table.header(
    table.cell(fill: spe-blue, text(fill: white, weight: "bold")[Aspect]),
    table.cell(fill: spe-blue, text(fill: white, weight: "bold")[Envoy (SPE-221987)]),
    table.cell(fill: spe-blue, text(fill: white, weight: "bold")[#clarissa]),
  ),
  
  table.hline(stroke: 0.5pt),
  
  [Primary Function], [Query existing models], [Generate complete decks],
  table.hline(stroke: 0.3pt + gray),
  [Interaction Mode], [Q&A on loaded model], [Elicitation dialogue],
  table.hline(stroke: 0.3pt + gray),
  [Simulator], [ECHELON (proprietary)], [OPM Flow (open source)],
  table.hline(stroke: 0.3pt + gray),
  [Architecture], [RAG + Callback Agents], [RL + Neuro-symbolic + Loop],
  table.hline(stroke: 0.3pt + gray),
  [Learning], [Static knowledge bases], [Adaptive via sim feedback],
  table.hline(stroke: 0.3pt + gray),
  [Availability], [Commercial license], [Web-based, license-free],
  table.hline(stroke: 0.3pt + gray),
  [Validation], [Post-hoc analysis], [Pre-execution physics check],
  
  table.hline(stroke: 0.5pt),
)

#v(1em)

// Development Phases
#text(size: 12pt, weight: "bold")[Development Phases]

#v(0.5em)

#block(inset: (left: 1cm))[
  *Phase I — Syntactic Assistance:* Deck generation from natural language, syntax validation, OPM Flow integration, basic error correction.
  
  *Phase II — Physics-Informed:* Simulator-in-loop learning, convergence optimization, sensitivity analysis, analog-based defaults.
  
  *Phase III — Field-Specialized:* Embedded operational agents, asset-specific tuning, real-time surveillance, autonomous workflows.
]

#v(2em)

#line(length: 100%, stroke: 0.5pt + gray)

#v(0.3em)

#text(size: 9pt, fill: gray)[
  Word Count: 448 | Prepared for SPE Europe Energy Conference 2026 | Generated #datetime.today().display()
]
