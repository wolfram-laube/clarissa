# ADR-021: CLARISSA Portal - System & Security Architecture

| Status | Proposed |
|--------|----------|
| Date | 2026-01-22 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-020 (Portal Vision), ADR-022 (Software Architecture), ADR-016 (Runner Load Balancing) |

---

## Context

CLARISSA requires a central portal for the distributed team (Schärding + Houston). The portal is being built during the experimental phase by ~4 developers, but should later be used productively by significantly more users.

This ADR defines:
1. **System Architecture**: Infrastruktur, Deployment, Services
2. **Security Architecture**: Authentication, Authorization, Session Management

The Software Architecture (Hexagonal Pattern, API Design, Code Structure) is documented in ADR-022.

---

## Decision

### Key Decisions

| Decision | Choice | Rationale |
|--------------|------|------------|
| **Compute** | Cloud Run (GCP) | Scale-to-zero, $0 Free Tier, Team-Zugang |
| **Local Dev** | OpenWhisk Standalone | Benchmarking, no GCP dependency for devs |
| **Database** | Firestore | Serverless, Free Tier, Document Model passt |
| **Storage** | GCS | PDFs, Standard, Free Tier |
| **Frontend Hosting** | GitLab Pages | Already available, $0 |
| **Auth Provider** | GitLab (OIDC) | Team already has GitLab accounts |
| **OAuth Flow** | Authorization Code + PKCE | Best Practice, Defense-in-Depth |

---

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GitLab Pages (Static Frontend)                       │
│                         https://clarissa.gitlab.io                           │
│  ┌────────────────────────────────────┬────────────────────────────────┐    │
│  │         Portal SPA (Alpine.js)     │        MkDocs Documentation    │    │
│  │  /                    Landing      │  /docs/           ADRs, Guides │    │
│  │  /portal/time         Time Track   │  /docs/notebooks  Jupyter      │    │
│  │  /portal/billing      Invoices     │                                │    │
│  │  /portal/benchmarks   Runner Grid  │                                │    │
│  └────────────────┬───────────────────┴────────────────────────────────┘    │
└───────────────────│─────────────────────────────────────────────────────────┘
                    │
                    │ REST API (authenticated)
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GCP Cloud Run (All Services)                         │
│                         Scale-to-Zero, $0/month (Free Tier)                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Portal API Service                                │    │
│  │  ┌───────────┬───────────┬─────────────┬─────────────────────────┐  │    │
│  │  │   Auth    │   Time    │  Benchmarks │    Billing (Light)      │  │    │
│  │  │  (OIDC)   │  (CRUD)   │   (Read)    │   (CRUD, Status)        │  │    │
│  │  │  ~200ms   │  ~100ms   │   ~150ms    │      ~100ms             │  │    │
│  │  └───────────┴───────────┴─────────────┴─────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                    ┌────────────────┼────────────────┐                       │
│                    │ async HTTP     │                │                       │
│                    ▼                ▼                ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Worker Service (Heavy Lifting)                    │    │
│  │  ┌─────────────────┬─────────────────┬─────────────────────────┐    │    │
│  │  │  billing/       │  benchmarks/    │       (extensible)      │    │    │
│  │  │  generate-pdf   │  aggregate      │                         │    │    │
│  │  │  ~30-60s        │  ~10-30s        │                         │    │    │
│  │  └─────────────────┴─────────────────┴─────────────────────────┘    │    │
│  │  Timeout: 15min │ Retry: 3x exponential │ Scale: 0-10               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                              ┌──────┴──────┐                                 │
│                              │  Firestore  │                                 │
│                              │   (NoSQL)   │                                 │
│                              └─────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Apache OpenWhisk (Linux Yoga) - LOCAL                     │
│                    Development & Benchmarking Only                           │
│  ┌─────────────────┬─────────────────┬─────────────────────────────────┐    │
│  │  billing/       │  benchmarks/    │       clarissa/                 │    │
│  │  generate-pdf   │  aggregate      │       simulate (Future)         │    │
│  │  (same core)    │  (same core)    │       (unbounded runtime)       │    │
│  └─────────────────┴─────────────────┴─────────────────────────────────┘    │
│                                                                              │
│  Setup: OpenWhisk Standalone (java -jar) OR K3s + Helm                      │
│  Purpose: Local dev, A/B benchmarking vs Cloud Run, Future simulations      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cloud Run Services

| Service | Purpose | Timeout | Memory | Public |
|---------|---------|---------|--------|--------|
| `clarissa-portal-api` | Auth, Time, Billing CRUD, Benchmarks | 30s | 512Mi | ✅ Yes |
| `clarissa-worker` | PDF Generation, Aggregation | 15min | 1Gi | ❌ No (IAM) |

```bash
# Portal API Deployment
gcloud run deploy clarissa-portal-api \
  --image=gcr.io/$PROJECT/clarissa-portal-api:$SHA \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --timeout=30 \
  --memory=512Mi \
  --set-env-vars="WORKER_URL=https://clarissa-worker-xxx.run.app"

# Worker Service Deployment
gcloud run deploy clarissa-worker \
  --image=gcr.io/$PROJECT/clarissa-worker:$SHA \
  --region=europe-west1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --timeout=900 \
  --memory=1Gi \
  --max-instances=10 \
  --min-instances=0
```

### OpenWhisk (Local Development)

For development and benchmarking on Linux Yoga:

```bash
# Option A: Standalone (recommended for dev)
# 1GB RAM, 2 Minuten Setup
java -jar openwhisk-standalone.jar

# Option B: K3s + Helm (for K8s overhead benchmarks)
# 4GB RAM, ~1h Setup
helm install owdev openwhisk/openwhisk -n openwhisk --create-namespace
```

### Team Distribution

| Rolle | Maschine | Cloud Run | OpenWhisk |
|-------|----------|-----------|-----------|
| Mike, Ian, Doug (Houston) | Any | ✅ Cloud Run only | ❌ Not needed |
| Wolfram (Schärding) | Linux Yoga | ✅ Cloud Run | ✅ OpenWhisk (Dev/Benchmark) |

---

## Security Architecture

### Access Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCESS MODEL                                         │
│                                                                              │
│   ┌───────────────────────────────────────┐                                 │
│   │     GitLab Pages (PUBLIC)             │                                 │
│   │                                       │                                 │
│   │  • Static HTML/JS/CSS                 │  ← Anyone can see               │
│   │  • No secrets, no sensitive data      │                                 │
│   │  • Login button redirects to OIDC     │                                 │
│   └───────────────────────────────────────┘                                 │
│                       │                                                      │
│                       │ API Calls (require valid session)                   │
│                       ▼                                                      │
│   ┌───────────────────────────────────────┐                                 │
│   │     Portal API (PROTECTED)            │                                 │
│   │                                       │                                 │
│   │  • All endpoints require auth         │  ← Only authenticated users    │
│   │  • Session via HttpOnly cookie        │                                 │
│   │  • CORS: only *.gitlab.io             │                                 │
│   └───────────────────────────────────────┘                                 │
│                       │                                                      │
│                       │ Service-to-Service (IAM)                            │
│                       ▼                                                      │
│   ┌───────────────────────────────────────┐                                 │
│   │     Worker Service (INTERNAL)         │                                 │
│   │                                       │                                 │
│   │  • No public access                   │  ← Only Portal API can call    │
│   │  • GCP IAM authentication             │                                 │
│   └───────────────────────────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Point:** GitLab Pages are public - this is OK because:
- No secrets in frontend code
- No API keys in JavaScript
- All sensitive data only via authenticated API calls

### GitLab als OIDC Provider

GitLab.com ist ein vollwertiger OpenID Connect Provider:

```
OIDC Discovery URL:
https://gitlab.com/.well-known/openid-configuration

Endpoints:
├── authorization: https://gitlab.com/oauth/authorize
├── token:         https://gitlab.com/oauth/token
├── userinfo:      https://gitlab.com/oauth/userinfo
└── jwks_uri:      https://gitlab.com/oauth/discovery/keys
```

### OAuth Flow: Authorization Code + PKCE

**Why PKCE even though we are a Confidential Client?**
- Defense-in-Depth: Protects against Authorization Code Interception
- Best Practice: OAuth 2.1 will require PKCE for all clients
- Future-proof: If we add mobile apps later
- No downside: Minimal overhead

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Authorization Code + PKCE Flow                            │
│                                                                              │
│   Browser              Portal API              GitLab OIDC                  │
│      │                     │                       │                        │
│      │ 1. Click Login      │                       │                        │
│      │────────────────────►│                       │                        │
│      │                     │                       │                        │
│      │                     │ Generate:             │                        │
│      │                     │ - code_verifier (random 32 bytes)              │
│      │                     │ - code_challenge = SHA256(verifier)            │
│      │                     │ - state (CSRF token)  │                        │
│      │                     │                       │                        │
│      │                     │ Store verifier in     │                        │
│      │                     │ Redis (TTL 10min)     │                        │
│      │                     │                       │                        │
│      │ 2. Redirect         │                       │                        │
│      │◄────────────────────│                       │                        │
│      │   Location: gitlab.com/oauth/authorize?     │                        │
│      │     response_type=code                      │                        │
│      │     client_id=xxx                           │                        │
│      │     redirect_uri=.../callback               │                        │
│      │     scope=openid+profile+email              │                        │
│      │     state=csrf_token                        │                        │
│      │     code_challenge=abc123...    ◄── PKCE    │                        │
│      │     code_challenge_method=S256  ◄── PKCE    │                        │
│      │                     │                       │                        │
│      │ 3. User Login + Consent                     │                        │
│      │─────────────────────┼──────────────────────►│                        │
│      │◄────────────────────┼───────────────────────│                        │
│      │                     │                       │                        │
│      │ 4. Redirect with code                       │                        │
│      │◄────────────────────┼───────────────────────│                        │
│      │   ?code=AUTH_CODE&state=csrf_token          │                        │
│      │                     │                       │                        │
│      │ 5. Send code to backend                     │                        │
│      │────────────────────►│                       │                        │
│      │                     │                       │                        │
│      │                     │ 6. Token Exchange     │                        │
│      │                     │──────────────────────►│                        │
│      │                     │   POST /oauth/token   │                        │
│      │                     │   code=AUTH_CODE      │                        │
│      │                     │   code_verifier=...  ◄── PKCE                  │
│      │                     │   client_id + secret  │                        │
│      │                     │                       │                        │
│      │                     │◄──────────────────────│                        │
│      │                     │   { access_token,     │                        │
│      │                     │     id_token,         │                        │
│      │                     │     refresh_token }   │                        │
│      │                     │                       │                        │
│      │                     │ 7. Validate id_token  │                        │
│      │                     │    - Signature (JWKS) │                        │
│      │                     │    - Issuer, Audience │                        │
│      │                     │    - Expiry           │                        │
│      │                     │                       │                        │
│      │ 8. Session Cookie   │                       │                        │
│      │◄────────────────────│                       │                        │
│      │   Set-Cookie: session=...; HttpOnly; Secure │                        │
│      │                     │                       │                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GitLab Application Setup

```
GitLab → User Settings → Applications → New Application

┌─────────────────────────────────────────────────────────────┐
│  Add new application                                         │
├─────────────────────────────────────────────────────────────┤
│  Name:          CLARISSA Portal                              │
│                                                              │
│  Redirect URI:  https://clarissa-portal-api-xxxxx.run.app   │
│                 /api/v1/auth/callback                        │
│                                                              │
│  Confidential:  ☑ Yes                                       │
│                                                              │
│  Scopes:        ☑ openid    (OIDC ID Token)                 │
│                 ☑ profile   (Name, Avatar)                  │
│                 ☑ email     (Email-Adresse)                 │
│                                                              │
│  [Save application]                                          │
├─────────────────────────────────────────────────────────────┤
│  → Application ID + Secret in GCP Secret Manager speichern  │
└─────────────────────────────────────────────────────────────┘
```

### Session Management

| Aspekt | Implementation |
|--------|----------------|
| **Session Token** | JWT, selbst signiert (HS256) |
| **Storage** | HttpOnly Cookie |
| **Lifetime** | 1 Stunde |
| **Refresh** | Via GitLab refresh_token (in Firestore) |
| **PKCE Verifier** | Redis mit 10min TTL |

### Service-to-Service Auth

Portal API → Worker:

```python
from google.auth.transport.requests import Request
from google.oauth2 import id_token

# Get GCP identity token for Worker service
auth_req = Request()
token = id_token.fetch_id_token(auth_req, WORKER_URL)

response = await client.post(
    f"{WORKER_URL}/worker/billing/generate-pdf",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Security Summary

| Aspect | Implementation |
|--------|----------------|
| **Identity Provider** | GitLab.com (OIDC) |
| **OAuth Flow** | Authorization Code + PKCE (S256) |
| **OIDC Scopes** | `openid profile email` |
| **Session Storage** | HttpOnly Cookie (JWT, 1h) |
| **Token Refresh** | GitLab refresh_token in Firestore |
| **PKCE Verifier** | Redis (10min TTL) |
| **CORS** | Restrict to `*.gitlab.io` |
| **CSRF Protection** | `state` parameter |
| **Secrets** | GCP Secret Manager |
| **Service Auth** | GCP IAM (Portal API → Worker) |

---

## CI/CD Pipeline

```yaml
# .gitlab-ci.yml (vereinfacht)

stages:
  - test
  - build
  - deploy
  - pages

variables:
  PORTAL_API_IMAGE: gcr.io/$GCP_PROJECT/clarissa-portal-api
  WORKER_IMAGE: gcr.io/$GCP_PROJECT/clarissa-worker
  REGION: europe-west1

build:portal-api:
  stage: build
  image: gcr.io/kaniko-project/executor:latest
  script:
    - /kaniko/executor
        --context=.
        --dockerfile=services/portal-api/Dockerfile
        --destination=$PORTAL_API_IMAGE:$CI_COMMIT_SHA
        --destination=$PORTAL_API_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes: [services/portal-api/**/*, shared/**/*]

build:worker:
  stage: build
  image: gcr.io/kaniko-project/executor:latest
  script:
    - /kaniko/executor
        --context=.
        --dockerfile=services/worker/Dockerfile
        --destination=$WORKER_IMAGE:$CI_COMMIT_SHA
        --destination=$WORKER_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes: [services/worker/**/*, shared/**/*]

deploy:portal-api:
  stage: deploy
  image: google/cloud-sdk:slim
  script:
    - echo "$GCP_SERVICE_KEY" | gcloud auth activate-service-account --key-file=-
    - gcloud run deploy clarissa-portal-api
        --image=$PORTAL_API_IMAGE:$CI_COMMIT_SHA
        --region=$REGION
        --platform=managed
        --allow-unauthenticated
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:worker:
  stage: deploy
  image: google/cloud-sdk:slim
  script:
    - echo "$GCP_SERVICE_KEY" | gcloud auth activate-service-account --key-file=-
    - gcloud run deploy clarissa-worker
        --image=$WORKER_IMAGE:$CI_COMMIT_SHA
        --region=$REGION
        --platform=managed
        --no-allow-unauthenticated
        --timeout=900
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

pages:
  stage: pages
  script:
    - pip install mkdocs mkdocs-material
    - mkdocs build --site-dir public/docs
    - cp -r frontend/portal/* public/
  artifacts:
    paths: [public]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Cost Analysis

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| **Cloud Run: Portal API** | $0 | Free tier: 2M requests |
| **Cloud Run: Worker** | $0 | Free tier: 180K vCPU-s |
| **Firestore** | $0 | Free tier: 1GB, 50K reads/day |
| **GCS** | ~$0.02 | 5GB free |
| **OpenWhisk** | $0 | Self-hosted (Linux Yoga) |
| **GitLab Pages** | $0 | Included |
| **Total** | **~$0/month** | Within free tiers |

### Scaling Projections

| Users | Requests/mo | Est. Cost |
|-------|-------------|-----------|
| 4 (dev) | ~30K | $0 |
| 50 | ~150K | $0 |
| 500 | ~1.5M | $0 |
| 1000+ | ~3M+ | ~$10+ |

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] GitLab Application registrieren
- [ ] Cloud Run Services skeleton (FastAPI)
- [ ] Firestore collections setup
- [ ] OIDC Auth flow mit PKCE implementieren

### Phase 2: Core Infrastructure (Week 3-4)
- [ ] Worker Service deployment
- [ ] Service-to-Service Auth (IAM)
- [ ] CI/CD Pipeline komplett

### Phase 3: OpenWhisk (Week 5)
- [ ] OpenWhisk Standalone auf Linux Yoga
- [ ] Benchmark-Vergleich Cloud Run vs OpenWhisk

---

## References

- [ADR-020: Portal Vision & Requirements](./ADR-020-portal-vision.md)
- [ADR-022: Portal Software Architecture](./ADR-022-portal-software-architecture.md)
- [GitLab as OpenID Connect Provider](https://docs.gitlab.com/ee/integration/openid_connect_provider.html)
- [OAuth 2.0 for Browser-Based Apps (PKCE)](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GCP IAM Service-to-Service Auth](https://cloud.google.com/run/docs/authenticating/service-to-service)