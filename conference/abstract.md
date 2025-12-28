# ORSA: A Physics-Centric AI Agent Architecture for Reservoir Simulation

ORSA is a phased AI agent architecture designed to augment reservoir simulation workflows through simulator-in-the-loop learning, physics-centric reasoning, and governed human interaction. Rather than replacing established simulators, ORSA integrates multiple reservoir simulators as heterogeneous sources of numerical and physical feedback, complemented by a lightweight native simulation kernel for controlled experiments, sensitivity analysis, and explainability.

Large language models provide planning, reasoning, and human-oriented interaction. Reinforcement learning is employed to optimize action sequences such as debugging and model refinement based on simulator-derived numerical outcomes, including convergence behavior and stability. Neuro-symbolic components act as a governance and constraint layer, enforcing engineering rules, escalation policies, and safety boundaries without serving as the primary learning mechanism.

ORSA evolves from syntactic assistance toward physics-informed reservoir engineering support and, ultimately, field-specialized agents embedded in operational teams.
