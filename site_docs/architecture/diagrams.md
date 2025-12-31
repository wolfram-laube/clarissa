# Architecture Diagrams

Visual representations of CLARISSA's architecture.

## Agent Flow

How a user request flows through the system:

```mermaid
flowchart TD
  U[User / Engineer] -->|proposal| A[CLARISSA Agent]
  A --> G{Governance Policy}
  G -->|approval required| H[Human Approval]
  H -->|approve| S[Simulator Adapter]
  G -->|no approval| S
  S --> K[Kernel/Explainer]
  K --> R[Recommendation / Rationale]
  R --> U
```

## Adapter Layer

How simulators are abstracted:

```mermaid
flowchart LR
    subgraph Adapters
        Mock[MockSimulator]
        OPM[OPM Flow]
        MRST[MRST]
    end
    
    subgraph Contract
        Run["run(deck) → dict"]
        Conv[converged: bool]
        Err[errors: list]
    end
    
    Agent[CLARISSA Agent] --> Contract
    Contract --> Adapters
```

## Governance Gate

The approval workflow:

```mermaid
flowchart TD
    P[Proposal] --> Check{requires_approval?}
    Check -->|yes| Request[request_approval]
    Check -->|no| Execute[Execute]
    Request -->|approved| Execute
    Request -->|denied| Reject[Reject]
    Execute --> Simulate[Run Simulator]
    Simulate --> Explain[Generate Explanation]
```

## CI Pipeline

The observability-focused CI model:

```mermaid
flowchart LR
    subgraph Test["Test Stage"]
        T1[tests]
        T2[contract_tests]
        T3[snapshot_tests]
        T4[governance_impact]
    end
    
    subgraph Classify["Classify Stage"]
        C1[ci_classify]
    end
    
    subgraph Auto["Automation Stage"]
        A1[mr_report]
        A2[issue_bot]
        A3[recovery_bot]
    end
    
    Test --> Classify
    Classify --> Auto
```

## Source Files

Mermaid sources are in `docs/architecture/diagrams/`:

- `agent_flow.mmd`
- `adapter_layer.mmd`
- `governance_gate.mmd`
- `ci_to_mr.mmd`

CI renders these to SVG when possible.
