# Architecture Overview

CLARISSA's architecture comprises six primary layers, each addressing distinct concerns while maintaining loose coupling through well-defined interfaces.

## System Layers

```mermaid
graph TB
    subgraph UI["User Interface Layer"]
        Voice[Voice Input]
        Chat[Text Chat]
        Web[Web Interface]
        API[REST API]
    end
    
    subgraph NLP["NLP Translation Layer"]
        ASR[Speech Recognition]
        Intent[Intent Recognition]
        Entity[Entity Extraction]
        Validate[Asset Validation]
        Syntax[Syntax Generation]
        Physics[Deck Validation]
    end
    
    subgraph Gateway["API Gateway"]
        Auth[Authentication]
        Route[Routing]
        Rate[Rate Limiting]
    end
    
    subgraph Orch["Orchestration Layer"]
        Queue[Job Queue]
        Workflow[Workflow Engine]
        Monitor[Monitoring]
    end
    
    subgraph AI["AI Inference Layer"]
        Router[Model Router]
        Registry[Model Registry]
        Serve[Model Serving]
    end
    
    subgraph Data["Data Mesh Layer"]
        Sim[(Simulation)]
        Train[(Training)]
        User[(User)]
        Graph[(Connectivity)]
        Cache[(Cache)]
    end
    
    UI --> Gateway
    Gateway --> NLP
    NLP --> Orch
    Orch --> AI
    AI --> Data
    Orch --> Data
```

## Core Principles

### 1. Configuration over Convention

Every major component supports runtime configuration:

- Database backends (Cassandra, MongoDB, PostgreSQL, Neo4j, Redis)
- Message brokers (Kafka, RabbitMQ, Redis Streams)
- Model serving (Ray Serve, Triton, custom)
- Authentication providers

### 2. Domain-Driven Decomposition

Service boundaries align with domain concepts:

| Domain | Responsibility | Storage |
|--------|---------------|---------|
| Simulation | Decks, results, time-series | Cassandra |
| Training | ML datasets, model artifacts | MongoDB |
| User | Auth, audit, preferences | PostgreSQL |
| Connectivity | Well relationships, flow paths | Neo4j |
| Cache | Sessions, hot data | Redis |

### 3. Event-Driven Integration

Asynchronous messaging decouples services:

- Long-running simulations don't block UI
- Progress updates via event streams
- Eventual consistency across domains

## NLP Translation Pipeline

The translation layer converts natural language to valid ECLIPSE syntax through six validated stages:

```mermaid
graph LR
    A[Speech] --> B[Intent]
    B --> C[Entity]
    C --> D[Asset]
    D --> E[Syntax]
    E --> F[Deck]
    
    B -.->|validate| B
    C -.->|validate| C
    D -.->|validate| D
    E -.->|validate| E
    F -.->|validate| F
```

Each stage has explicit validation. Failed validation triggers rollback, not silent errors.

See [ADR-009](adr/ADR-009-nlp-translation-pipeline.md) for details.

## Deployment Scenarios

### Air-Gapped

- Locally-hosted open-source models
- Self-contained infrastructure
- Offline update via secure media

### Cloud-Native

- Managed Kubernetes
- Managed databases
- Auto-scaling

**Same code, different configuration.**

## Related ADRs

- [ADR-001: Physics-Centric Architecture](adr/ADR-001-physics-centric.md)
- [ADR-002: Separation of Roles](adr/ADR-002-separation-of-roles.md)
- [ADR-003: Native Kernel](adr/ADR-003-native-kernel.md)
- [ADR-009: NLP Pipeline](adr/ADR-009-nlp-translation-pipeline.md)
