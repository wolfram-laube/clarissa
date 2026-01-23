# ADR-020: CLARISSA Portal - Vision & Requirements

| Status | Proposed |
|--------|----------|
| Date | 2026-01-23 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-021 (System & Security Architecture), ADR-022 (Software Architecture), ADR-016 (Runner Load Balancing) |

---

## 1 Context

### 1.1 Current State

CLARISSA is evolving as a distributed research project with a team spread across two continents:

| Person | Location | Timezone | Role | Infrastructure |
|--------|----------|----------|------|----------------|
| Wolfram | Schärding, AT | CET (UTC+1) | Lead, Admin | Mac #1, Mac #2, Linux Yoga (local), GCP VM |
| Mike | Houston, US | CST (UTC-6) | Consultant | Laptop |
| Ian | Houston, US | CST (UTC-6) | Consultant | Laptop |
| Doug | Houston, US | CST (UTC-6) | Consultant | Laptop |

The physical CI/CD runners (3 local machines) are located in Schärding, while the GCP-based system (`gitlab-runner`, europe-west3-a) runs centrally. This distribution creates operational challenges:

1. **Observability Gap**: The 12-runner matrix (4 machines × 3 executors) requires centralized monitoring
2. **Time Tracking Friction**: GitLab Issues as workaround for consultant time tracking
3. **Billing Overhead**: Manual PDF generation and Google Drive upload via CI/CD pipeline
4. **Documentation Fragmentation**: MkDocs exists, but without interactive dashboards

### 1.2 Problem Statement

Without a central portal, CLARISSA lacks a platform that:

- Enables team-wide collaboration independent of timezones
- Provides operational awareness of CI/CD state
- Consolidates administrative tasks (billing, time tracking)
- Serves as entry point for new team members and later external users

---

## 2 Scope

This document defines the **vision, requirements, and principles** for the CLARISSA Portal. It serves as reference for:

- [ADR-021: System & Security Architecture](./ADR-021-portal-system-security-architecture.md) - Infrastructure, Deployment, Auth
- [ADR-022: Software Architecture](./ADR-022-portal-software-architecture.md) - Hexagonal Pattern, API Design, Code Structure

**In Scope:**
- Portal vision and strategic goals
- Functional and non-functional requirements
- Architecture principles and guardrails
- Ecosystem integration

**Out of Scope:**
- Technical implementation details (→ ADR-021, ADR-022)
- API specifications (→ ADR-022)
- Security details (→ ADR-021)

---

## 3 Vision

### 3.1 Portal Purpose

The CLARISSA Portal is the **central coordination and observability interface** for the distributed team. It abstracts the complexity of the multi-runner infrastructure and consolidates operational workflows.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLARISSA Ecosystem                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    User-Facing Layer                                 │    │
│  │                                                                      │    │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │    │
│  │   │    Portal       │    │     MkDocs      │    │    GitLab      │  │    │
│  │   │  (This ADR)     │    │  Documentation  │    │   Repository   │  │    │
│  │   │                 │    │                 │    │                │  │    │
│  │   │  • Dashboards   │    │  • ADRs         │    │  • Code        │  │    │
│  │   │  • Time Track   │    │  • Guides       │    │  • Issues      │  │    │
│  │   │  • Billing      │    │  • Tutorials    │    │  • CI/CD       │  │    │
│  │   │  • Benchmarks   │    │  • API Docs     │    │  • Registry    │  │    │
│  │   └────────┬────────┘    └────────┬────────┘    └───────┬────────┘  │    │
│  │            │                      │                     │           │    │
│  └────────────┼──────────────────────┼─────────────────────┼───────────┘    │
│               │                      │                     │                │
│  ┌────────────┼──────────────────────┼─────────────────────┼───────────┐    │
│  │            ▼                      ▼                     ▼           │    │
│  │                    Infrastructure Layer                              │    │
│  │                                                                      │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │              12-Runner CI/CD Matrix                          │   │    │
│  │   │                                                              │   │    │
│  │   │   Mac #1      Mac #2      Linux Yoga    GCP VM              │   │    │
│  │   │   ┌─────┐     ┌─────┐     ┌─────┐       ┌─────┐             │   │    │
│  │   │   │Shell│     │Shell│     │Shell│       │Shell│             │   │    │
│  │   │   │Docker│    │Docker│    │Docker│      │Docker│            │   │    │
│  │   │   │K8s  │     │K8s  │     │K8s  │       │K8s  │             │   │    │
│  │   │   └─────┘     └─────┘     └─────┘       └─────┘             │   │    │
│  │   │                                                              │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Target Users

| User Persona | Needs | Portal Features |
|--------------|-------|-----------------|
| **Wolfram (Admin)** | Billing, runner monitoring, time review | All features + admin views |
| **Consultants (Mike, Ian, Doug)** | Time entry, view own invoices | Time tracking, billing (read) |
| **Future: External Users** | Simulation access, results | Public landing + auth |

### 3.3 Evolutionary Phases

Evolutionary development in three phases:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Portal Evolution Phases                                  │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   Phase 1        │  │   Phase 2        │  │   Phase 3        │          │
│  │   Team Tools     │  │   Operational    │  │   External       │          │
│  │                  │  │                  │  │                  │          │
│  │   Current Focus  │  │   Next Phase     │  │   Future Vision  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                    │
│           ▼                     ▼                     ▼                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ • Time Tracking  │  │ • Runner Health  │  │ • User Mgmt      │          │
│  │ • Billing        │  │ • Alert System   │  │ • Simulation UI  │          │
│  │ • Basic Metrics  │  │ • Trend Analysis │  │ • Result Viewer  │          │
│  │ • GitLab OIDC    │  │ • Cost Tracking  │  │ • Public API     │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4 Requirements

### 4.1 Functional Requirements

#### FR-1: Time Tracking
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Consultant can create time entries (date, duration, project, task) | Must |
| FR-1.2 | Consultant can edit/delete own time entries | Must |
| FR-1.3 | Admin can view all time entries | Must |
| FR-1.4 | Aggregated view per week/month | Should |

#### FR-2: Billing
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Admin can generate invoice from time entries | Must |
| FR-2.2 | System generates PDF automatically (async) | Must |
| FR-2.3 | PDF is stored in cloud storage | Must |
| FR-2.4 | Contractor can view own invoices | Should |

#### FR-3: Benchmarks (Runner Monitoring)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Dashboard shows current status of all 12 runners | Must |
| FR-3.2 | Historical pipeline durations per runner | Should |
| FR-3.3 | Anomaly detection for deviations | Could |

#### FR-4: Authentication
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Login via GitLab (OIDC) | Must |
| FR-4.2 | No separate user registration | Must |
| FR-4.3 | Session management with auto-refresh | Must |

### 4.2 Non-Functional Requirements

| ID | Requirement | Target | Rationale |
|----|-------------|--------|-----------|
| NFR-1 | **Availability** | 99% (excl. maintenance) | Team-critical, but not 24/7 operation |
| NFR-2 | **Latency** | < 500ms for CRUD, < 60s for PDF | Acceptable UX |
| NFR-3 | **Cost** | $0/month (Free Tier) | Budget constraint during experimental phase |
| NFR-4 | **Scalability** | 4 → 50 users without architecture change | Growth path |
| NFR-5 | **Security** | OIDC, HTTPS, HttpOnly Cookies | Industry best practice |
| NFR-6 | **Portability** | Platform-agnostic core | Air-gap deployment option |

---

## 5 Design Principles

Based on established microservices and platform engineering principles:

### 5.1 Service-Based Approach

Instead of a monolith, the portal structures its functionality into logical services:

| Service | Responsibility | Coupling |
|---------|----------------|----------|
| **Auth Service** | OIDC flow, session management | Standalone |
| **Time Service** | CRUD for time entries | → Auth |
| **Billing Service** | Invoice generation, PDF | → Time, Auth |
| **Benchmark Service** | Runner metrics, aggregation | → Auth |

### 5.2 Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Hexagonal Architecture Principle                          │
│                                                                              │
│   "The business logic is platform-independent in the shared/ directory.     │
│    Thin adapters translate between platform (Cloud Run, OpenWhisk)          │
│    and core."                                                                │
│                                                                              │
│                         ┌─────────────────┐                                  │
│                         │   Shared Core   │                                  │
│                         │  (Pure Python)  │                                  │
│                         │                 │                                  │
│                         │  • Business     │                                  │
│                         │    Logic        │                                  │
│                         │  • Models       │                                  │
│                         │  • Validation   │                                  │
│                         └────────┬────────┘                                  │
│                                  │                                           │
│              ┌───────────────────┼───────────────────┐                       │
│              │                   │                   │                       │
│              ▼                   ▼                   ▼                       │
│   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│   │  Cloud Run       │ │  OpenWhisk       │ │  Future:         │            │
│   │  Adapter         │ │  Adapter         │ │  K8s Jobs        │            │
│   └──────────────────┘ └──────────────────┘ └──────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Rationale:** This architecture enables:
- Platform switching without core code changes
- A/B benchmarking between deployments
- Air-gapped installation for security-sensitive environments

### 5.3 Zero-Infrastructure for Consultants

| Team Member | Infrastructure Responsibility |
|-------------|-------------------------------|
| Wolfram | GCP, GitLab, Runners, Portal Deployment |
| Mike, Ian, Doug | **None** - only browser + GitLab login |

**Principle:** Houston team needs no local setup, no API keys, no cloud credentials.

### 5.4 Observability by Design

Three-tier observability architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Portal Observability                                      │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                 Cloud Run Metrics (GCP)                           │     │
│   │   • Request count, latency, errors                                │     │
│   │   • Cold starts                                                   │     │
│   │   • Memory/CPU usage                                              │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                     │                                        │
│                                     ▼                                        │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                 Application Metrics (Custom)                      │     │
│   │   • Benchmark pipeline durations                                  │     │
│   │   • PDF generation times                                          │     │
│   │   • Active sessions                                               │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                     │                                        │
│                                     ▼                                        │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                 Portal Dashboard (User-Facing)                    │     │
│   │   • Runner health grid                                            │     │
│   │   • Trend charts                                                  │     │
│   │   • Alerts                                                        │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 Progressive Enhancement

The portal complements existing tools, does not replace them:

| Capability | Current Tool | Portal Enhancement |
|------------|--------------|-------------------|
| Time Tracking | GitLab Issues | Dedicated UI, aggregation |
| Billing | CI/CD Pipeline | Async generation, status tracking |
| Documentation | MkDocs | Unified entry point |
| CI Monitoring | GitLab UI | Consolidated dashboard |

---

## 6 Constraints & Guardrails

### 6.1 Technical Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.11+ | Team skills, FastAPI ecosystem |
| GCP Free Tier | Budget during experimental phase |
| GitLab OIDC | No separate identity management |
| Static Frontend (GitLab Pages) | $0, already available |

### 6.2 Architectural Guardrails

Mandatory architecture rules:

| Guardrail | Rule |
|-----------|------|
| **No Secrets in Frontend** | GitLab Pages is public - all sensitive data only via auth'd API |
| **Core Must Be Platform-Agnostic** | `shared/` has no cloud-specific imports |
| **Adapters Are Thin** | Max 50 LOC per adapter, logic belongs in core |
| **Explicit Defaults** | All assumptions documented, no magic values |

### 6.3 Security Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Trust Boundaries                                          │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PUBLIC (No Auth Required)                                          │   │
│   │                                                                      │   │
│   │  • GitLab Pages static content                                      │   │
│   │  • MkDocs documentation                                             │   │
│   │  • Login button                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│                              OIDC Auth                                       │
│                                     │                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  AUTHENTICATED (Valid Session Required)                             │   │
│   │                                                                      │   │
│   │  • All Portal API endpoints                                         │   │
│   │  • Time entries (own data)                                          │   │
│   │  • Invoices (own data)                                              │   │
│   │  • Benchmark dashboards                                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│                              Role Check                                      │
│                                     │                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ADMIN (Role = admin)                                               │   │
│   │                                                                      │   │
│   │  • All user time entries                                            │   │
│   │  • Invoice generation                                               │   │
│   │  • System configuration                                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7 Air-Gapped Deployment Option

For future scenarios (e.g., enterprise customers without cloud access):

| Component | Cloud | Air-Gapped |
|-----------|-------|------------|
| Compute | Cloud Run | K3s + Deployment |
| Database | Firestore | SQLite/PostgreSQL |
| Storage | GCS | Local filesystem |
| Auth | GitLab.com OIDC | Self-hosted GitLab / Local auth |
| Serverless | Cloud Run Jobs | OpenWhisk / faasd |

**Hexagonal architecture makes this possible:** Core logic remains identical, only adapters are swapped.

---

## 8 Success Criteria

| Metric | Phase 1 Target | Measurement |
|--------|----------------|-------------|
| **Adoption** | 4/4 team members use portal | Login analytics |
| **Time Tracking** | 90% of hours tracked via portal | DB query |
| **Billing Automation** | 100% of invoices via portal | Manual count |
| **Runner Visibility** | Dashboard shows all 12 runners | Visual check |
| **Cost** | $0/month | GCP billing |

---

## 9 Decision

**We build the CLARISSA Portal** as central team interface with:

1. **Service-Based Architecture** (Auth, Time, Billing, Benchmarks)
2. **Hexagonal Core** for platform portability
3. **GCP Cloud Run** as primary deployment platform
4. **GitLab OIDC** for authentication
5. **Progressive Enhancement** of existing tools

Details see:
- [ADR-021: System & Security Architecture](./ADR-021-portal-system-security-architecture.md)
- [ADR-022: Software Architecture](./ADR-022-portal-software-architecture.md)

---

## 10 References

- [ADR-016: Runner Load Balancing](./ADR-016-runner-load-balancing.md)
- [ADR-017: GDrive Folder Structure](./ADR-017-gdrive-folder-structure.md)
- [ADR-019: Billing Folder Structure](./ADR-019-billing-folder-structure.md)
- [Hexagonal Architecture - Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Microservices Patterns - Chris Richardson](https://microservices.io/patterns/)