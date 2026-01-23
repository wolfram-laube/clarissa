# ADR-022: CLARISSA Portal - Software Architecture

| Status | Proposed |
|--------|----------|
| Date | 2026-01-22 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-021 (System & Security Architecture), ADR-020 (Portal Vision) |

---

## Context

ADR-021 defines the system and security architecture of the CLARISSA Portal (Cloud Run, OIDC, etc.). This ADR describes the software architecture:

1. **Hexagonal Architecture**: Platform-agnostic core with adapters
2. **API Design**: Endpoints, Contracts, Error Handling
3. **Data Model**: Firestore Collections
4. **Frontend**: Alpine.js SPA

---

## Decision

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Architecture Pattern** | Hexagonal (Ports & Adapters) | Platform portability, testability |
| **Core Language** | Python 3.11+ | Team skills, FastAPI, async |
| **API Framework** | FastAPI | Async, Pydantic, OpenAPI |
| **Frontend** | Alpine.js + HTMX | Lightweight, no build step |
| **Styling** | Tailwind CSS | Utility-first, fast iteration |

---

## Hexagonal Architecture

### Principle

The business logic is platform-independent in the `shared/` directory. Thin adapters translate between platform (Cloud Run, OpenWhisk) and core.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Shared Core (Pure Python)                        │
│                         Platform-agnostic Business Logic                 │
│                                                                          │
│   shared/                                                                │
│   ├── billing/                                                           │
│   │   ├── pdf_generator.py      # Jinja2 + WeasyPrint                   │
│   │   ├── invoice_calculator.py # Line items, totals                    │
│   │   └── models.py             # Pydantic Models                        │
│   │                                                                      │
│   ├── benchmarks/                                                        │
│   │   ├── aggregator.py         # Stats computation                     │
│   │   └── anomaly_detector.py   # Deviation detection                   │
│   │                                                                      │
│   └── core/                                                              │
│       ├── retry.py              # Retry strategy                        │
│       └── correlation.py        # Request correlation                   │
│                                                                          │
└──────────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   OpenWhisk Adapter         │   │   Cloud Run Adapter         │
│                             │   │                             │
│   def main(args: dict):     │   │   @app.post("/worker/...")  │
│     result = core.run(...)  │   │   async def handler(req):   │
│     return {"body": result} │   │     return core.run(...)    │
│                             │   │                             │
│   JSON in → JSON out        │   │   HTTP Request/Response     │
└─────────────────────────────┘   └─────────────────────────────┘
```

### Benefits

- **Same Core Code**: Write business logic once, test once
- **Platform Portability**: Switch platforms without code changes
- **Benchmarking**: Apples-to-apples comparison Cloud Run vs OpenWhisk
- **Testability**: Core testable without HTTP/containers

---

## Project Structure

```
clarissa-portal/
│
├── shared/                            # ⭐ Platform-agnostic Core
│   ├── __init__.py
│   ├── core/
│   │   ├── retry.py                   # Retry strategy (tenacity)
│   │   ├── correlation.py             # Correlation ID handling
│   │   └── exceptions.py              # Domain exceptions
│   │
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py           # Core: Jinja2 + WeasyPrint
│   │   ├── invoice_calculator.py      # Core: Line items, totals
│   │   ├── models.py                  # Pydantic: Invoice, LineItem
│   │   └── templates/
│   │       └── invoice.html           # Jinja2 Template
│   │
│   └── benchmarks/
│       ├── __init__.py
│       ├── aggregator.py              # Core: Stats computation
│       ├── anomaly_detector.py        # Core: Deviation detection
│       └── models.py                  # Pydantic: BenchmarkResult
│
├── services/                          # Cloud Run Services
│   ├── portal-api/
│   │   ├── src/
│   │   │   ├── main.py                # FastAPI entry
│   │   │   ├── config.py              # Settings (Pydantic)
│   │   │   ├── core/
│   │   │   │   ├── auth.py            # OIDC + PKCE
│   │   │   │   ├── middleware.py      # CORS, Logging, Correlation
│   │   │   │   └── dependencies.py    # FastAPI Dependencies
│   │   │   ├── api/v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── time.py
│   │   │   │   ├── billing.py
│   │   │   │   └── benchmarks.py
│   │   │   └── services/
│   │   │       └── worker_client.py   # HTTP client to Worker
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── worker/
│       ├── src/
│       │   ├── main.py
│       │   ├── billing/
│       │   │   └── generate_pdf.py    # Adapter → shared/billing
│       │   └── benchmarks/
│       │       └── aggregate.py       # Adapter → shared/benchmarks
│       ├── Dockerfile
│       └── requirements.txt
│
├── adapters/                          # OpenWhisk (Local Dev)
│   └── openwhisk/
│       ├── billing/
│       │   └── __main__.py            # def main(args) → dict
│       └── benchmarks/
│           └── __main__.py
│
├── frontend/
│   └── portal/                        # SPA (Alpine.js)
│       ├── index.html
│       ├── time/index.html
│       ├── billing/index.html
│       ├── benchmarks/index.html
│       └── assets/
│           ├── js/
│           │   ├── app.js             # Alpine.js Store
│           │   ├── api.js             # Fetch wrapper
│           │   └── auth.js            # OAuth flow
│           └── css/
│               └── portal.css
│
└── tests/
    ├── shared/                        # ⭐ Test Core once
    │   ├── test_pdf_generator.py
    │   └── test_aggregator.py
    ├── services/
    │   └── test_api.py
    └── e2e/
        └── test_full_flow.py
```

---

## Core Implementation Examples

### Billing: PDF Generator

```python
# shared/billing/pdf_generator.py

from jinja2 import Environment, PackageLoader
from weasyprint import HTML
from .models import Invoice

class InvoicePDFGenerator:
    """
    Platform-agnostic PDF generation.
    No HTTP, no Firestore - pure business logic.
    """
    
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('shared.billing', 'templates')
        )
        self.template = self.env.get_template('invoice.html')
    
    def generate(self, invoice: Invoice) -> bytes:
        """
        Generate PDF bytes from Invoice model.
        
        Args:
            invoice: Validated Invoice model
            
        Returns:
            PDF as bytes
        """
        html_content = self.template.render(
            invoice=invoice,
            line_items=invoice.line_items,
            total=invoice.calculate_total(),
            vat=invoice.calculate_vat()
        )
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
```

### Adapter: Cloud Run Worker

```python
# services/worker/src/billing/generate_pdf.py

from fastapi import APIRouter, BackgroundTasks
from shared.billing.pdf_generator import InvoicePDFGenerator
from shared.billing.models import Invoice

router = APIRouter()

@router.post("/worker/billing/generate-pdf")
async def generate_pdf(invoice_id: str, background_tasks: BackgroundTasks):
    """
    Cloud Run adapter for PDF generation.
    Handles HTTP, Firestore, GCS - delegates logic to shared core.
    """
    background_tasks.add_task(generate_pdf_task, invoice_id)
    return {"status": "accepted", "invoice_id": invoice_id}


async def generate_pdf_task(invoice_id: str):
    db = get_firestore_client()
    storage = get_gcs_client()
    
    # Update status
    await db.update_invoice(invoice_id, {"status": "processing"})
    
    try:
        # Load data
        invoice_data = await db.get_invoice(invoice_id)
        invoice = Invoice(**invoice_data)
        
        # Core logic (platform-agnostic)
        generator = InvoicePDFGenerator()
        pdf_bytes = generator.generate(invoice)
        
        # Upload to GCS
        pdf_url = await storage.upload(
            f"invoices/{invoice_id}.pdf",
            pdf_bytes,
            content_type="application/pdf"
        )
        
        # Update status
        await db.update_invoice(invoice_id, {
            "status": "ready",
            "pdf_url": pdf_url
        })
        
    except Exception as e:
        await db.update_invoice(invoice_id, {
            "status": "failed",
            "error": str(e)
        })
        raise
```

### Adapter: OpenWhisk Action

```python
# adapters/openwhisk/billing/__main__.py

from shared.billing.pdf_generator import InvoicePDFGenerator
from shared.billing.models import Invoice

def main(args: dict) -> dict:
    """
    OpenWhisk adapter for PDF generation.
    Same core logic, different platform wrapper.
    """
    try:
        invoice_data = args.get("invoice")
        invoice = Invoice(**invoice_data)
        
        generator = InvoicePDFGenerator()
        pdf_bytes = generator.generate(invoice)
        
        # Base64 encode for JSON response
        import base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode()
        
        return {
            "statusCode": 200,
            "body": {
                "pdf_base64": pdf_base64,
                "filename": f"invoice-{invoice.id}.pdf"
            }
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }
```

---

## API Design

### Endpoints

```
Base: https://clarissa-portal-api-xxxxx.run.app/api/v1

Auth
├── GET  /auth/login              → GitLab OIDC redirect
├── GET  /auth/callback           → OAuth callback
├── POST /auth/refresh            → Refresh session
├── POST /auth/logout             → Clear session
└── GET  /auth/me                 → Current user

Time Entries
├── GET    /time/entries          → List (paginated)
├── POST   /time/entries          → Create
├── GET    /time/entries/{id}     → Get one
├── PUT    /time/entries/{id}     → Update
├── DELETE /time/entries/{id}     → Delete
└── GET    /time/summary          → Aggregated stats

Billing
├── GET  /billing/invoices              → List invoices
├── POST /billing/invoices              → Create draft
├── GET  /billing/invoices/{id}         → Get (incl. status)
├── PUT  /billing/invoices/{id}         → Update draft
├── POST /billing/invoices/{id}/generate-pdf  → Trigger async
│        └── Returns: 202 Accepted { status: "queued" }
└── GET  /billing/invoices/{id}/pdf     → Redirect to GCS

Benchmarks
├── GET  /benchmarks/latest       → Latest per runner
├── GET  /benchmarks/history      → Time range query
└── POST /benchmarks/ingest       → CI posts results
```

### Request/Response Contract

```python
# shared/billing/models.py

from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from enum import Enum

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class LineItem(BaseModel):
    description: str
    hours: Decimal = Field(ge=0)
    rate: Decimal = Field(ge=0)
    
    @property
    def amount(self) -> Decimal:
        return self.hours * self.rate

class Invoice(BaseModel):
    id: str
    client_id: str
    contractor_id: str
    period_start: date
    period_end: date
    line_items: list[LineItem]
    status: InvoiceStatus = InvoiceStatus.DRAFT
    pdf_url: str | None = None
    error: str | None = None
    
    def calculate_total(self) -> Decimal:
        return sum(item.amount for item in self.line_items)
    
    def calculate_vat(self, rate: Decimal = Decimal("0.20")) -> Decimal:
        return self.calculate_total() * rate
```

---

## Error Handling

### Status State Machine

```
         ┌─────────┐
         │  draft  │
         └────┬────┘
              │ POST .../generate-pdf
              ▼
         ┌─────────┐
         │ queued  │
         └────┬────┘
              │ Worker picks up
              ▼
       ┌──────────────┐
       │  processing  │
       └──────┬───────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌─────────┐      ┌──────────┐
│  ready  │      │  failed  │
└─────────┘      └────┬─────┘
                      │ retry_count < 3
                      ▼
                 ┌─────────┐
                 │ queued  │ (retry)
                 └─────────┘
```

### Retry Strategy

```python
# shared/core/retry.py

from tenacity import retry, stop_after_attempt, wait_exponential

RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=4, max=60),
    "reraise": True
}

@retry(**RETRY_CONFIG)
async def execute_with_retry(func, *args, **kwargs):
    return await func(*args, **kwargs)
```

### API Error Responses

```python
# Standard error response format

{
    "error": {
        "code": "INVOICE_NOT_FOUND",
        "message": "Invoice INV-001 not found",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

# HTTP Status Codes
# 400 - Validation error (bad input)
# 401 - Not authenticated
# 403 - Not authorized
# 404 - Resource not found
# 409 - Conflict (e.g., invoice already processing)
# 500 - Internal error (with correlation_id for debugging)
```

---

## Data Model (Firestore)

```
firestore/
├── users/
│   └── {user_id}/
│       ├── gitlab_id: string
│       ├── email: string
│       ├── name: string
│       ├── avatar_url: string
│       ├── role: "admin" | "user"
│       ├── refresh_token: string (encrypted)
│       └── created_at: timestamp
│
├── time_entries/
│   └── {entry_id}/
│       ├── user_id: string
│       ├── project: string
│       ├── task: string
│       ├── duration_hours: number
│       ├── date: date
│       ├── notes: string
│       └── created_at: timestamp
│
├── invoices/
│   └── {invoice_id}/
│       ├── client_id: string
│       ├── contractor_id: string
│       ├── period_start: date
│       ├── period_end: date
│       ├── line_items: array
│       ├── status: string
│       ├── pdf_url: string | null
│       ├── error: string | null
│       ├── retry_count: number
│       └── timestamps...
│
└── benchmarks/
    └── {benchmark_id}/
        ├── runner_id: string
        ├── executor: "shell" | "docker" | "k8s"
        ├── machine: string
        ├── pipeline_id: string
        ├── job_id: string
        ├── duration_seconds: number
        ├── status: "success" | "failed"
        └── timestamp: timestamp
```

### Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Users can only read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    
    match /time_entries/{entryId} {
      allow read, write: if request.auth.uid == resource.data.user_id;
      allow create: if request.auth.uid == request.resource.data.user_id;
    }
    
    // Invoices: contractors can see their own
    match /invoices/{invoiceId} {
      allow read: if request.auth.uid == resource.data.contractor_id;
      allow write: if request.auth.uid == resource.data.contractor_id 
                   && resource.data.status == "draft";
    }
    
    // Benchmarks: anyone authenticated can read, only CI can write
    match /benchmarks/{benchmarkId} {
      allow read: if request.auth != null;
      allow write: if false; // Only via Admin SDK
    }
  }
}
```

---

## Frontend Architecture

### Tech Stack

- **Alpine.js**: Reactive UI (15KB, no build step)
- **HTMX**: HTML-over-the-wire (optional, for simple interactions)
- **Tailwind CSS**: Utility-first styling
- **Chart.js**: Benchmark visualizations

### Structure

```html
<!-- frontend/portal/index.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <title>CLARISSA Portal</title>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="/assets/js/app.js"></script>
</head>
<body x-data="app" class="bg-gray-100">
    
    <!-- Navigation -->
    <nav class="bg-white shadow" x-show="$store.auth.isAuthenticated">
        <a href="/portal/">Dashboard</a>
        <a href="/portal/time/">Time</a>
        <a href="/portal/billing/">Billing</a>
        <a href="/portal/benchmarks/">Benchmarks</a>
        <button @click="$store.auth.logout()">Logout</button>
    </nav>
    
    <!-- Login -->
    <div x-show="!$store.auth.isAuthenticated" class="flex items-center justify-center h-screen">
        <button @click="$store.auth.login()" class="btn-primary">
            Login with GitLab
        </button>
    </div>
    
    <!-- Content -->
    <main x-show="$store.auth.isAuthenticated">
        <!-- Page content loaded here -->
    </main>
    
</body>
</html>
```

### Alpine.js Store

```javascript
// frontend/portal/assets/js/app.js

const API_BASE = 'https://clarissa-portal-api-xxxxx.run.app/api/v1';

document.addEventListener('alpine:init', () => {
    
    // Auth Store
    Alpine.store('auth', {
        user: null,
        isAuthenticated: false,
        
        async init() {
            await this.checkSession();
        },
        
        async checkSession() {
            try {
                const res = await fetch(`${API_BASE}/auth/me`, { 
                    credentials: 'include' 
                });
                if (res.ok) {
                    this.user = await res.json();
                    this.isAuthenticated = true;
                }
            } catch (e) {
                this.isAuthenticated = false;
            }
        },
        
        login() {
            window.location.href = `${API_BASE}/auth/login`;
        },
        
        async logout() {
            await fetch(`${API_BASE}/auth/logout`, { 
                method: 'POST', 
                credentials: 'include' 
            });
            this.isAuthenticated = false;
            window.location.href = '/';
        }
    });
    
    // API Helper
    Alpine.magic('api', () => ({
        async get(endpoint) {
            const res = await fetch(`${API_BASE}${endpoint}`, { 
                credentials: 'include' 
            });
            if (!res.ok) throw new Error(`API Error: ${res.status}`);
            return res.json();
        },
        
        async post(endpoint, data) {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error(`API Error: ${res.status}`);
            return res.json();
        }
    }));
});
```

---

## Implementation Roadmap

### Phase 1: Core (Week 1-2)
- [ ] `shared/` module structure
- [ ] Pydantic models
- [ ] PDF generator (Jinja2 + WeasyPrint)
- [ ] Unit tests for Core

### Phase 2: Services (Week 3-4)
- [ ] Portal API endpoints
- [ ] Worker Service
- [ ] Firestore integration
- [ ] Error handling + retry

### Phase 3: Frontend (Week 5)
- [ ] Alpine.js setup
- [ ] Auth flow (Login/Logout)
- [ ] Time tracking UI
- [ ] Billing UI

### Phase 4: Polish (Week 6)
- [ ] Benchmark dashboard
- [ ] E2E tests
- [ ] Documentation

---

## References

- [ADR-021: Portal System & Security Architecture](./ADR-021-portal-system-security-architecture.md)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
