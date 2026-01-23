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

CLARISSA entwickelt sich als dezentrales Forschungsprojekt mit einem Team verteilt über zwei Kontinente:

| Person | Location | Timezone | Rolle | Infrastruktur |
|--------|----------|----------|-------|---------------|
| Wolfram | Schärding, AT | CET (UTC+1) | Lead, Admin | Mac #1, Mac #2, Linux Yoga (lokal), GCP VM |
| Mike | Houston, US | CST (UTC-6) | Consultant | Laptop |
| Ian | Houston, US | CST (UTC-6) | Consultant | Laptop |
| Doug | Houston, US | CST (UTC-6) | Consultant | Laptop |

Die physischen CI/CD-Runner (3 lokale Maschinen) stehen in Schärding, während das GCP-basierte System (`gitlab-runner`, europe-west3-a) zentralisiert läuft. Diese Verteilung bringt operative Herausforderungen:

1. **Observability Gap**: Die 12-Runner-Matrix (4 Maschinen × 3 Executors) erfordert zentrale Überwachung
2. **Time Tracking Friction**: GitLab Issues als Workaround für Consultant-Zeiterfassung
3. **Billing Overhead**: Manuelle PDF-Generierung und Google Drive Upload via CI/CD-Pipeline
4. **Documentation Fragmentation**: MkDocs existiert, aber ohne interaktive Dashboards

### 1.2 Problem Statement

Ohne ein zentrales Portal fehlt CLARISSA eine Plattform, die:

- Team-übergreifende Zusammenarbeit unabhängig von Zeitzonen ermöglicht
- Operational Awareness über den CI/CD-Zustand bietet
- Administrative Aufgaben (Billing, Time Tracking) konsolidiert
- Als Einstiegspunkt für neue Team-Mitglieder und später externe User dient

---

## 2 Scope

Dieses Dokument definiert die **Vision, Anforderungen und Prinzipien** für das CLARISSA Portal. Es dient als Referenz für:

- [ADR-021: System & Security Architecture](./ADR-021-portal-system-security-architecture.md) - Infrastruktur, Deployment, Auth
- [ADR-022: Software Architecture](./ADR-022-portal-software-architecture.md) - Hexagonal Pattern, API Design, Code Structure

**In Scope:**
- Portal Vision und strategische Ziele
- Funktionale und nicht-funktionale Anforderungen
- Architektur-Prinzipien und Guardrails
- Ecosystem-Integration

**Out of Scope:**
- Technische Implementierungsdetails (→ ADR-021, ADR-022)
- API-Spezifikationen (→ ADR-022)
- Security-Details (→ ADR-021)

---

## 3 Vision

### 3.1 Portal Purpose

Das CLARISSA Portal ist das **zentrale Koordinations- und Observability-Interface** für das verteilte Team. Es abstrahiert die Komplexität der Multi-Runner-Infrastruktur und konsolidiert operative Workflows.

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
| **Wolfram (Admin)** | Billing, Runner Monitoring, Time Review | All features + Admin views |
| **Consultants (Mike, Ian, Doug)** | Time entry, eigene Invoices sehen | Time Tracking, Billing (read) |
| **Future: External Users** | Simulation access, Results | Public landing + Auth |

### 3.3 Evolutionary Phases

Evolutionary development in drei Phasen:

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
| FR-1.1 | Consultant kann Zeiteinträge erfassen (Datum, Dauer, Projekt, Aufgabe) | Must |
| FR-1.2 | Consultant kann eigene Zeiteinträge bearbeiten/löschen | Must |
| FR-1.3 | Admin kann alle Zeiteinträge einsehen | Must |
| FR-1.4 | Aggregierte Ansicht pro Woche/Monat | Should |

#### FR-2: Billing
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Admin kann Invoice aus Zeiteinträgen generieren | Must |
| FR-2.2 | System generiert PDF automatisch (async) | Must |
| FR-2.3 | PDF wird in Cloud Storage abgelegt | Must |
| FR-2.4 | Contractor kann eigene Invoices einsehen | Should |

#### FR-3: Benchmarks (Runner Monitoring)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Dashboard zeigt aktuellen Status aller 12 Runner | Must |
| FR-3.2 | Historische Pipeline-Dauern pro Runner | Should |
| FR-3.3 | Anomalie-Erkennung bei Abweichungen | Could |

#### FR-4: Authentication
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Login via GitLab (OIDC) | Must |
| FR-4.2 | Keine separate User-Registrierung | Must |
| FR-4.3 | Session-Management mit Auto-Refresh | Must |

### 4.2 Non-Functional Requirements

| ID | Requirement | Target | Rationale |
|----|-------------|--------|-----------|
| NFR-1 | **Availability** | 99% (excl. maintenance) | Team-kritisch, aber kein 24/7-Betrieb |
| NFR-2 | **Latency** | < 500ms für CRUD, < 60s für PDF | Akzeptable UX |
| NFR-3 | **Cost** | $0/month (Free Tier) | Budget-Constraint während Experimental-Phase |
| NFR-4 | **Scalability** | 4 → 50 User ohne Architektur-Änderung | Wachstumspfad |
| NFR-5 | **Security** | OIDC, HTTPS, HttpOnly Cookies | Industry Best Practice |
| NFR-6 | **Portability** | Plattform-agnostischer Core | Air-Gap Deployment Option |

---

## 5 Design Principles

Basierend auf etablierten Microservices- und Platform-Engineering-Prinzipien:

### 5.1 Service-Based Approach

Statt eines Monolithen strukturiert das Portal seine Funktionalität in logische Services:

| Service | Responsibility | Coupling |
|---------|----------------|----------|
| **Auth Service** | OIDC Flow, Session Management | Standalone |
| **Time Service** | CRUD für Zeiteinträge | → Auth |
| **Billing Service** | Invoice Generation, PDF | → Time, Auth |
| **Benchmark Service** | Runner Metrics, Aggregation | → Auth |

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

**Rationale:** Diese Architektur ermöglicht:
- Plattform-Wechsel ohne Core-Code-Änderungen
- A/B-Benchmarking zwischen Deployments
- Air-Gapped Installation für security-sensitive Umgebungen

### 5.3 Zero-Infrastructure für Consultants

| Team Member | Infrastructure Responsibility |
|-------------|-------------------------------|
| Wolfram | GCP, GitLab, Runners, Portal Deployment |
| Mike, Ian, Doug | **Keine** - nur Browser + GitLab Login |

**Prinzip:** Houston-Team braucht keinen lokalen Setup, keine API-Keys, keine Cloud-Credentials.

### 5.4 Observability by Design

Dreistufige Observability-Architektur:

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

Das Portal ergänzt bestehende Tools, ersetzt sie nicht:

| Capability | Current Tool | Portal Enhancement |
|------------|--------------|-------------------|
| Time Tracking | GitLab Issues | Dedizierte UI, Aggregation |
| Billing | CI/CD Pipeline | Async Generation, Status Tracking |
| Documentation | MkDocs | Unified Entry Point |
| CI Monitoring | GitLab UI | Consolidated Dashboard |

---

## 6 Constraints & Guardrails

### 6.1 Technical Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.11+ | Team-Skills, FastAPI Ecosystem |
| GCP Free Tier | Budget während Experimental-Phase |
| GitLab OIDC | Keine separate Identity Management |
| Static Frontend (GitLab Pages) | $0, bereits vorhanden |

### 6.2 Architectural Guardrails

Verbindliche Architektur-Regeln:

| Guardrail | Rule |
|-----------|------|
| **No Secrets in Frontend** | GitLab Pages ist public - alle sensiblen Daten nur via Auth'd API |
| **Core Must Be Platform-Agnostic** | `shared/` hat keine Cloud-spezifischen Imports |
| **Adapters Are Thin** | Max 50 LOC pro Adapter, Logik gehört in Core |
| **Explicit Defaults** | Alle Annahmen dokumentiert, keine Magic Values |

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

Für zukünftige Szenarien (z.B. Enterprise-Kunden ohne Cloud-Zugang):

| Component | Cloud | Air-Gapped |
|-----------|-------|------------|
| Compute | Cloud Run | K3s + Deployment |
| Database | Firestore | SQLite/PostgreSQL |
| Storage | GCS | Local Filesystem |
| Auth | GitLab.com OIDC | Self-hosted GitLab / Local Auth |
| Serverless | Cloud Run Jobs | OpenWhisk / faasd |

**Hexagonal Architecture macht dies möglich:** Core-Logik bleibt identisch, nur Adapter werden getauscht.

---

## 8 Success Criteria

| Metric | Phase 1 Target | Measurement |
|--------|----------------|-------------|
| **Adoption** | 4/4 Team Members nutzen Portal | Login Analytics |
| **Time Tracking** | 90% der Stunden via Portal erfasst | DB Query |
| **Billing Automation** | 100% der Invoices via Portal | Manual count |
| **Runner Visibility** | Dashboard zeigt alle 12 Runner | Visual check |
| **Cost** | $0/month | GCP Billing |

---

## 9 Decision

**Wir bauen das CLARISSA Portal** als zentrales Team-Interface mit:

1. **Service-Based Architecture** (Auth, Time, Billing, Benchmarks)
2. **Hexagonal Core** für Plattform-Portabilität
3. **GCP Cloud Run** als primäre Deployment-Plattform
4. **GitLab OIDC** für Authentication
5. **Progressive Enhancement** der bestehenden Tools

Details siehe:
- [ADR-021: System & Security Architecture](./ADR-021-portal-system-security-architecture.md)
- [ADR-022: Software Architecture](./ADR-022-portal-software-architecture.md)

---

## 10 References

- [ADR-016: Runner Load Balancing](./ADR-016-runner-load-balancing.md)
- [ADR-017: GDrive Folder Structure](./ADR-017-gdrive-folder-structure.md)
- [ADR-019: Billing Folder Structure](./ADR-019-billing-folder-structure.md)
- [Hexagonal Architecture - Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Microservices Patterns - Chris Richardson](https://microservices.io/patterns/)