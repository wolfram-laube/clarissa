# Architecture Diagrams

Mermaid sources live in `docs/architecture/diagrams/*.mmd`.

## Diagrams

### Adapter Layer

```mermaid
flowchart LR
  A[CLARISSA Agent] --> C[Simulator Contract]
  C --> M[MockSimulator]
  C --> MRST[MRST Adapter]
  C --> OPM[OPM Flow Adapter]
  MRST -. planned .-> MR[MATLAB Runtime]
  OPM -. planned .-> F[flow executable / container]
```

### Agent Flow

```mermaid
flowchart LR
  U[User] -->|proposal| A[CLARISSA]
  A --> G{Policy}
  G -->|needs approval| H[Human]
  H -->|ok| S[Simulator]
  G -->|auto| S
  S --> R[Result]
  R --> U
```

### CI to MR Flow

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant CI as GitLab CI
  participant MR as Merge Request
  Dev->>CI: push / update MR
  CI->>CI: run tests, rerun last-failed
  CI->>CI: classify flaky vs confirmed
  CI->>CI: run snapshot_tests + contract_tests
  CI-->>MR: unified MR note (status + summaries)
  CI-->>MR: export reports/mr_report.md/html (artifact)
```

### Governance Gate

```mermaid
flowchart TD
  P[Proposed Change] --> D{Touches governed params}
  D -->|Yes| A[Approval required]
  A -->|Approved| E[Execute simulation]
  A -->|Denied| X[Stop or escalate]
  D -->|No| E
  E --> O[Outcome and Explanation]
```

---

!!! info "Source files"
    The `.mmd` sources in `diagrams/` are the canonical truth.
    Edit those files to update diagrams.
