# ADR-041: Voice Service Extraction as Shared Blauweiss Capability

**Status:** Proposed  
**Date:** 2026-02-28  
**Deciders:** Wolfram Laube, Claude (AI Assistant)  
**Related:** ADR-005 (Single Repo), ADR-028 (Voice Input Architecture), ADR-031 (Portal Location Strategy), ADR-024 (CLARISSA Core)

---

## Context

CLARISSA's voice input capability has grown organically across three locations in the monorepo:

| Location | Content | Tech Stack |
|----------|---------|------------|
| `src/clarissa/voice/` | Backend pipeline: capture, transcribe, VAD, intent, execute | Python |
| `src/clarissa/voice/static/` | Standalone HTML voice capture | HTML/JS |
| `src/portal/components/voice/` + `recording/` | Portal-integrated voice UI | React/TSX |

This duplication creates maintenance burden and unclear ownership. More importantly, voice input is no longer a CLARISSA-only concern. The capability is needed for:

1. **CLARISSA** — Reservoir simulation commands ("Set permeability to 150 mD")
2. **Operations Portal** — Business operations ("Show applications from last week")
3. **Future projects** — Any Blauweiss product requiring voice-first interaction

ADR-005 defined triggers for repo decomposition: *"architecture stabilizes, prototype becomes reusable by others, independent release cadence required."* ADR-031 defined a similar trigger: *"Zweites Produkt/Projekt in Produktion."* Both triggers are now met.

### Key Architectural Insight

The voice pipeline (ADR-028) has a natural decomposition boundary **after transcription**:

```
[Audio Capture] → [STT/Whisper] → [Transcript]  ← SHARED (domain-agnostic)
                                        ↓
                                  [Intent Parsing] → [Command Mapping] → [Execute]  ← PROJECT-SPECIFIC
```

Everything up to and including transcription is domain-agnostic. Intent interpretation is inherently project-specific — reservoir vocabulary differs fundamentally from operations vocabulary.

Additionally, STT (Whisper) is compute-intensive and benefits from centralized deployment, while UI components are frontend artifacts that benefit from package distribution.

## Decision

Extract voice capabilities into **two new repositories** under the Blauweiss LLC group:

### 1. `blauweiss_llc/voice-service` — Microservice (Python)

Stateless microservice: audio in → transcript out.

```
voice-service/
├── src/
│   ├── api/                  # REST endpoint: POST /transcribe
│   ├── stt/                  # Whisper integration
│   ├── vad/                  # Voice Activity Detection
│   └── config.py
├── tests/
├── Dockerfile
├── helm/                     # K8s deployment chart
├── .gitlab-ci.yml
└── README.md
```

**Interface Contract:**

```
POST /v1/transcribe
Content-Type: multipart/form-data

Request:  { audio: <binary>, format: "webm"|"wav", language?: "en"|"de" }
Response: { transcript: string, confidence: float, duration_ms: int, language: string }
```

**Deployment:** Single instance on GCP Nordic VM or K8s cluster, shared by all consumers.

### 2. `blauweiss_llc/voice-ui` — Shared Component Library (npm)

Reusable frontend components for any Blauweiss application.

```
voice-ui/
├── src/
│   ├── VoiceInput.tsx        # Mic button + waveform visualization
│   ├── RecorderToolbar.tsx   # Recording controls
│   ├── VoiceResponseBanner.tsx
│   ├── useVoiceCapture.ts    # Hook: mic access, WebAudio, chunking
│   └── index.ts              # Public API
├── package.json
├── tsconfig.json
├── .gitlab-ci.yml            # Build + publish to GitLab npm registry
└── README.md
```

**Usage by consumers:**

```typescript
import { VoiceInput, useVoiceCapture } from '@blauweiss/voice-ui';

// VoiceInput handles mic access, visualization, and sends audio
// to the voice-service endpoint. Returns transcript to the consumer.
<VoiceInput
  serviceUrl="https://voice.blauweiss.dev/v1/transcribe"
  onTranscript={(text) => handleIntent(text)}
/>
```

### 3. Consumers retain intent interpretation

Each project keeps only the domain-specific mapping:

**CLARISSA** (`src/clarissa/voice/`):
- `intent.py` — Maps transcript to simulation commands
- `execute.py` — Executes against simulation engine
- Taxonomy: `agent/intents/taxonomy.json`

**Operations Portal** (`src/portal/`):
- `voice/intent.ts` — Maps transcript to ops actions (search applications, generate invoice, etc.)

### Resulting Group Structure

```
blauweiss_llc/
├── voice-service/            # Microservice — audio → text
├── voice-ui/                 # npm package — shared React components
├── irena/                    # CLARISSA — consumes both, owns sim intents
└── (future: ops/, magnus/)   # Other projects — consume both, own their intents
```

## Rationale

1. **Domain-agnostic cut.** The voice-service knows nothing about reservoirs or job applications. This is the cleanest possible decomposition boundary — it aligns with the natural pipeline stages from ADR-028.

2. **Microservice where it matters.** STT/Whisper is GPU-hungry and stateless — textbook microservice candidate. Centralizing it avoids duplicate compute costs and lets us upgrade Whisper once for all consumers.

3. **Library where it matters.** UI components are build-time dependencies, not runtime services. An npm package is the right distribution mechanism, not a REST call.

4. **Consistent with ADR precedent.** ADR-005 said "split when reusable by others" — voice is now reusable. ADR-031 said "split when second project needs it" — operations portal is that second project.

5. **Independent release cadence.** Voice-service can ship Whisper upgrades without touching CLARISSA. Voice-UI can ship component fixes without redeploying the service.

## Consequences

### Positive
- Clean ownership: voice team owns service + UI, project teams own intent mapping
- Single deployment for STT — cost-efficient, easy to upgrade
- Any future Blauweiss project gets voice capability "for free"
- CLARISSA repo shrinks — clearer focus on simulation domain
- Independent CI pipelines — frontend build doesn't block Python tests

### Negative
- Two new repos to maintain (CI, releases, versioning)
- Network dependency: consumers need voice-service reachable
- Initial migration effort to extract and rewire

### Neutral / Open
- Authentication strategy for voice-service TBD (API key? mTLS? same-cluster trust?)
- Whether voice-ui publishes to GitLab Package Registry or npmjs.com
- Streaming vs. batch transcription (batch first, streaming as P2)

## Alternatives Considered

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| **Keep in CLARISSA monorepo** | Rejected | Violates single-responsibility; portal would import from research repo |
| **Single `voice` repo (service + UI combined)** | Rejected | Different tech stacks (Python vs. TypeScript), different release cycles |
| **Voice as pure SDK (no microservice)** | Rejected | Whisper is too resource-heavy for client-side; wastes compute if embedded in each consumer |
| **Voice-service only (no UI library)** | Possible | But leads to copy-paste of React components across projects |

## Migration Plan

### Phase 1: Scaffold (Week 1)
- Create `blauweiss_llc/voice-service` and `blauweiss_llc/voice-ui` repos
- Set up CI pipelines (Docker build + Helm for service, npm build for UI)
- Define and document API contract

### Phase 2: Extract (Week 2)
- Move `src/clarissa/voice/{capture,transcribe,vad,api}.py` → voice-service
- Move `src/portal/components/voice/*` + `src/clarissa/voice/static/*` → voice-ui
- Consolidate duplicate recording components

### Phase 3: Wire (Week 3)
- CLARISSA: `pip install blauweiss-voice-client` or direct REST calls to service
- Portal: `npm install @blauweiss/voice-ui`
- Update CLARISSA `src/clarissa/voice/` to only retain `intent.py` + `execute.py`

### Phase 4: Cleanup (Week 4)
- Remove migrated files from CLARISSA repo
- Update ADR-028 status to "Superseded by ADR-041"
- Deploy voice-service to GCP Nordic VM
- Verify end-to-end: Portal voice → transcribe → ops action

## Notes
- The voice-service should support health checks (`GET /health`) for K8s liveness/readiness probes
- Consider WebSocket endpoint (`/v1/stream`) as future enhancement for real-time transcription
- Domain-specific vocabulary boosting (e.g., Whisper `initial_prompt` with reservoir terms) can be passed as a request parameter, keeping the service domain-agnostic while allowing consumers to improve accuracy
