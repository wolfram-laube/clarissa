# ADR-025: CLARISSA LLM Integration Strategy

| Status | Proposed |
|--------|----------|
| Date | 2026-01-22 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-024 (Core System Architecture), ADR-009 (NLP Translation Pipeline) |

---

## Context

CLARISSA ist ein **Conversational** User Interface - LLM-Calls sind der Kern des Systems, nicht ein Add-on. Die Architektur muss unterstützen:

1. **Cloud Deployment**: SaaS, API-basierte LLMs (Claude, GPT, Gemini)
2. **On-Premise**: Enterprise-Kunden mit Datenschutz-Anforderungen
3. **Air-Gapped**: Öl-Majors, Regierungen, kritische Infrastruktur - kein Internet

Zusätzlich: Verschiedene Tasks brauchen verschiedene Models (Intent → klein/schnell, Deck Generation → groß/präzise).

---

## Decision

### LLM Abstraction Layer (LAL)

Analog zum Simulator Abstraction Layer (SAL) in ADR-024:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLARISSA Core                                       │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     LLM Abstraction Layer (LAL)                          │   │
│   │                                                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │                    LLMInterface (Abstract)                       │   │   │
│   │   │                                                                  │   │   │
│   │   │   chat(messages, config) -> Response                            │   │   │
│   │   │   stream(messages, config) -> AsyncIterator[Token]              │   │   │
│   │   │   embed(texts) -> list[Vector]                                  │   │   │
│   │   │   get_capabilities() -> ModelCapabilities                       │   │   │
│   │   └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │                    ModelRouter                                   │   │   │
│   │   │                                                                  │   │   │
│   │   │   route(task: TaskType, requirements: Requirements) -> LLM      │   │   │
│   │   │   with_fallback(primary: LLM, fallback: LLM) -> LLM            │   │   │
│   │   └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│        ┌──────────────┬──────────────┬──────────────┬──────────────┐            │
│        │              │              │              │              │            │
│        ▼              ▼              ▼              ▼              ▼            │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐         │
│   │Anthropic│   │ OpenAI  │   │ Ollama  │   │  vLLM   │   │ Custom  │         │
│   │ Adapter │   │ Adapter │   │ Adapter │   │ Adapter │   │ Adapter │         │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Scenarios

### Scenario 1: Cloud (SaaS)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
│                                                                  │
│   User ──► CLARISSA (Cloud Run) ──► Anthropic API (Claude)      │
│                      │                                           │
│                      └──────────► OpenAI API (GPT) [fallback]   │
│                                                                  │
│   ✓ Best models available                                       │
│   ✓ No infrastructure management                                │
│   ✓ Pay-per-use                                                 │
│   ✗ Data leaves your network                                    │
│   ✗ Vendor dependency                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Use Cases:** Startups, Academics, Non-sensitive data

### Scenario 2: Hybrid (On-Premise LLM, Cloud optional)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ENTERPRISE NETWORK                           │
│                                                                  │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                    On-Premise                          │     │
│   │                                                        │     │
│   │   User ──► CLARISSA ──► Ollama/vLLM ──► Llama 3.1 70B │     │
│   │                │                                       │     │
│   │                │        GPU Server (A100/H100)         │     │
│   │                │                                       │     │
│   └────────────────│───────────────────────────────────────┘     │
│                    │                                             │
│                    │ (optional, für spezielle Tasks)            │
│                    ▼                                             │
│              ┌──────────┐                                        │
│              │ Internet │──► Claude API (mit Approval)          │
│              └──────────┘                                        │
│                                                                  │
│   ✓ Data stays on-premise (default)                             │
│   ✓ Cloud für spezielle Tasks (opt-in)                          │
│   ✓ Compliance-friendly                                         │
│   ✗ GPU Hardware nötig                                          │
│   ✗ Model Updates selbst managen                                │
└─────────────────────────────────────────────────────────────────┘
```

**Use Cases:** Enterprise, Data-sensitive projects, GDPR-relevant

### Scenario 3: Air-Gapped (Fully Isolated)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ISOLATED NETWORK                             │
│                     (No Internet Connection)                     │
│                                                                  │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                                                        │     │
│   │   User ──► CLARISSA ──► Ollama ──► Mistral/Llama      │     │
│   │                │                                       │     │
│   │                ├──► Embeddings ──► nomic-embed-text   │     │
│   │                │                                       │     │
│   │                └──► Code Gen ──► CodeLlama            │     │
│   │                                                        │     │
│   │   ┌────────────────────────────────────────────────┐  │     │
│   │   │  Local GPU Server                              │  │     │
│   │   │  - Ollama / vLLM / llama.cpp                   │  │     │
│   │   │  - Models: pre-downloaded, verified            │  │     │
│   │   │  - No external calls                           │  │     │
│   │   └────────────────────────────────────────────────┘  │     │
│   │                                                        │     │
│   └───────────────────────────────────────────────────────┘     │
│                                                                  │
│   ✓ Complete data isolation                                     │
│   ✓ No external dependencies at runtime                         │
│   ✓ Audit-friendly                                              │
│   ✗ Limited to local model capabilities                         │
│   ✗ Significant hardware investment                             │
└─────────────────────────────────────────────────────────────────┘
```

**Use Cases:** Oil Majors, Government, Defense, Critical Infrastructure

---

## Model Router: Task-Based Selection

Nicht jeder Task braucht das größte Model:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Model Router                                        │
│                                                                                  │
│   Task                        Model Size      Latency    Example Models         │
│   ─────────────────────────────────────────────────────────────────────────     │
│                                                                                  │
│   Intent Classification       Small (1-7B)    <100ms     Llama 3.2 3B           │
│   ├── "build model"                                      Mistral 7B             │
│   ├── "run simulation"                                   Claude Haiku           │
│   └── "explain results"                                                         │
│                                                                                  │
│   Slot Filling / NER          Small (1-7B)    <100ms     Llama 3.2 3B           │
│   ├── Extract: depth=8500ft                              SpaCy (non-LLM)        │
│   └── Extract: porosity=0.2                                                     │
│                                                                                  │
│   Deck Generation             Large (70B+)    1-5s       Llama 3.1 70B          │
│   ├── Complex reasoning                                  Claude Sonnet          │
│   └── Syntax precision                                   GPT-4                  │
│                                                                                  │
│   Explanation / Teaching      Medium (7-30B)  <1s        Llama 3.1 8B           │
│   ├── "Why did pressure drop?"                           Claude Haiku           │
│   └── "Explain WELSPECS"                                 Mistral 22B            │
│                                                                                  │
│   Embeddings                  Specialized     <50ms      nomic-embed-text       │
│   ├── Document retrieval                                 text-embedding-3       │
│   └── Similarity search                                  BGE-large              │
│                                                                                  │
│   Code Generation             Medium (7-30B)  <2s        CodeLlama 34B          │
│   ├── Python scripts                                     DeepSeek Coder         │
│   └── MATLAB/Octave                                      Claude Sonnet          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Interface Definition

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import AsyncIterator

class TaskType(Enum):
    INTENT_CLASSIFICATION = "intent"
    SLOT_FILLING = "slots"
    DECK_GENERATION = "deck_gen"
    EXPLANATION = "explain"
    EMBEDDING = "embed"
    CODE_GENERATION = "code_gen"

class DeploymentMode(Enum):
    CLOUD = "cloud"           # API calls to external providers
    ON_PREMISE = "on_prem"    # Local server, optional cloud
    AIR_GAPPED = "air_gap"    # No external connectivity

@dataclass
class ModelCapabilities:
    name: str
    provider: str
    context_window: int
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    max_output_tokens: int
    tasks: list[TaskType]

@dataclass
class LLMConfig:
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: list[str] | None = None
    
@dataclass 
class Message:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class Response:
    content: str
    model: str
    usage: dict  # tokens used
    finish_reason: str


class LLMInterface(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def chat(
        self, 
        messages: list[Message], 
        config: LLMConfig | None = None
    ) -> Response:
        """Synchronous chat completion."""
        ...
    
    @abstractmethod
    async def stream(
        self, 
        messages: list[Message], 
        config: LLMConfig | None = None
    ) -> AsyncIterator[str]:
        """Streaming chat completion."""
        ...
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        ...
    
    @abstractmethod
    def get_capabilities(self) -> ModelCapabilities:
        """Return model capabilities."""
        ...


class ModelRouter:
    """Route tasks to appropriate models based on requirements."""
    
    def __init__(self, deployment_mode: DeploymentMode):
        self.mode = deployment_mode
        self._providers: dict[str, LLMInterface] = {}
        self._task_mapping: dict[TaskType, str] = {}
    
    def register(self, name: str, provider: LLMInterface):
        """Register an LLM provider."""
        self._providers[name] = provider
    
    def set_task_model(self, task: TaskType, provider_name: str):
        """Map a task to a specific provider."""
        self._task_mapping[task] = provider_name
    
    def get_for_task(self, task: TaskType) -> LLMInterface:
        """Get the appropriate LLM for a task."""
        provider_name = self._task_mapping.get(task)
        if not provider_name:
            raise ValueError(f"No model configured for task: {task}")
        return self._providers[provider_name]
    
    def with_fallback(
        self, 
        primary: LLMInterface, 
        fallback: LLMInterface
    ) -> LLMInterface:
        """Wrap provider with fallback."""
        return FallbackLLM(primary, fallback)
```

---

## Provider Adapters

### Anthropic (Cloud)

```python
class AnthropicAdapter(LLMInterface):
    """Adapter for Anthropic Claude API."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def chat(self, messages: list[Message], config: LLMConfig | None = None) -> Response:
        config = config or LLMConfig()
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages]
        )
        
        return Response(
            content=response.content[0].text,
            model=self.model,
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
            finish_reason=response.stop_reason
        )
    
    async def stream(self, messages: list[Message], config: LLMConfig | None = None) -> AsyncIterator[str]:
        config = config or LLMConfig()
        
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=config.max_tokens,
            messages=[{"role": m.role, "content": m.content} for m in messages]
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Anthropic doesn't have embeddings, use voyageai or similar
        raise NotImplementedError("Use dedicated embedding model")
    
    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            name=self.model,
            provider="anthropic",
            context_window=200000,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            max_output_tokens=8192,
            tasks=[TaskType.DECK_GENERATION, TaskType.EXPLANATION, TaskType.CODE_GENERATION]
        )
```

### Ollama (On-Premise / Air-Gapped)

```python
class OllamaAdapter(LLMInterface):
    """Adapter for Ollama (local LLM server)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:70b"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(base_url=base_url, timeout=300)
    
    async def chat(self, messages: list[Message], config: LLMConfig | None = None) -> Response:
        config = config or LLMConfig()
        
        response = await self.client.post("/api/chat", json={
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            }
        })
        data = response.json()
        
        return Response(
            content=data["message"]["content"],
            model=self.model,
            usage={"total": data.get("eval_count", 0)},
            finish_reason="stop"
        )
    
    async def stream(self, messages: list[Message], config: LLMConfig | None = None) -> AsyncIterator[str]:
        config = config or LLMConfig()
        
        async with self.client.stream("POST", "/api/chat", json={
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": config.temperature}
        }) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if content := data.get("message", {}).get("content"):
                        yield content
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            response = await self.client.post("/api/embeddings", json={
                "model": "nomic-embed-text",
                "prompt": text
            })
            embeddings.append(response.json()["embedding"])
        return embeddings
    
    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            name=self.model,
            provider="ollama",
            context_window=128000,  # Llama 3.1
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,  # Depends on model
            max_output_tokens=4096,
            tasks=[TaskType.INTENT_CLASSIFICATION, TaskType.DECK_GENERATION, TaskType.EXPLANATION]
        )
```

### vLLM (High-Performance On-Premise)

```python
class VLLMAdapter(LLMInterface):
    """Adapter for vLLM (high-performance inference server)."""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        # vLLM exposes OpenAI-compatible API
        self.client = openai.AsyncOpenAI(
            base_url=f"{base_url}/v1",
            api_key="not-needed"  # vLLM doesn't require auth by default
        )
    
    async def chat(self, messages: list[Message], config: LLMConfig | None = None) -> Response:
        config = config or LLMConfig()
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        
        return Response(
            content=response.choices[0].message.content,
            model=self.model,
            usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens},
            finish_reason=response.choices[0].finish_reason
        )
    
    # stream() and embed() similar to above...
```

---

## Fallback Strategy

```python
class FallbackLLM(LLMInterface):
    """Wrapper that falls back to secondary provider on failure."""
    
    def __init__(self, primary: LLMInterface, fallback: LLMInterface):
        self.primary = primary
        self.fallback = fallback
    
    async def chat(self, messages: list[Message], config: LLMConfig | None = None) -> Response:
        try:
            return await self.primary.chat(messages, config)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}, falling back")
            return await self.fallback.chat(messages, config)
```

### Fallback Chains by Deployment

```python
def create_router(mode: DeploymentMode) -> ModelRouter:
    router = ModelRouter(mode)
    
    if mode == DeploymentMode.CLOUD:
        # Primary: Claude, Fallback: GPT
        claude = AnthropicAdapter(api_key=ANTHROPIC_KEY)
        gpt = OpenAIAdapter(api_key=OPENAI_KEY)
        
        router.register("claude", claude)
        router.register("gpt", gpt)
        router.register("claude_with_fallback", FallbackLLM(claude, gpt))
        
        router.set_task_model(TaskType.DECK_GENERATION, "claude_with_fallback")
        router.set_task_model(TaskType.INTENT_CLASSIFICATION, "claude")  # Haiku
        
    elif mode == DeploymentMode.ON_PREMISE:
        # Primary: Local Ollama, Optional Cloud fallback
        ollama = OllamaAdapter(model="llama3.1:70b")
        
        router.register("ollama", ollama)
        router.set_task_model(TaskType.DECK_GENERATION, "ollama")
        
        if ALLOW_CLOUD_FALLBACK:
            claude = AnthropicAdapter(api_key=ANTHROPIC_KEY)
            router.register("cloud_fallback", FallbackLLM(ollama, claude))
            router.set_task_model(TaskType.DECK_GENERATION, "cloud_fallback")
    
    elif mode == DeploymentMode.AIR_GAPPED:
        # Only local models, no fallback to cloud
        ollama_large = OllamaAdapter(model="llama3.1:70b")
        ollama_small = OllamaAdapter(model="llama3.2:3b")
        
        router.register("large", ollama_large)
        router.register("small", ollama_small)
        
        router.set_task_model(TaskType.DECK_GENERATION, "large")
        router.set_task_model(TaskType.INTENT_CLASSIFICATION, "small")
    
    return router
```

---

## Context Management

### RAG Integration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Context Pipeline                                         │
│                                                                                  │
│   User Query                                                                    │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     Vector Store (Embeddings)                            │   │
│   │                                                                          │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│   │   │  Simulator  │  │   Eclipse   │  │   SPE       │  │   User      │   │   │
│   │   │    Docs     │  │   Keywords  │  │   Papers    │  │   History   │   │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│   │                                                                          │   │
│   │   Storage: Qdrant / Chroma / pgvector (depending on deployment)         │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       │ Top-K relevant chunks                                                   │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     Context Assembly                                     │   │
│   │                                                                          │   │
│   │   System Prompt + Retrieved Context + Conversation History + User Query │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     LLM (via LAL)                                        │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Vector Store by Deployment

| Deployment | Vector Store | Notes |
|------------|--------------|-------|
| **Cloud** | Pinecone / Qdrant Cloud | Managed, scalable |
| **On-Premise** | Qdrant / Weaviate | Self-hosted, Docker |
| **Air-Gapped** | Chroma / pgvector | Embedded, no network |

---

## Hardware Requirements

### On-Premise / Air-Gapped GPU Sizing

| Model Size | VRAM Required | Example GPU | Throughput |
|------------|---------------|-------------|------------|
| 3-7B | 8-16 GB | RTX 4090, A10 | ~50 tok/s |
| 13B | 24-32 GB | A10G, L40 | ~30 tok/s |
| 70B | 80-140 GB | A100 80GB, 2xH100 | ~20 tok/s |
| 70B (quantized) | 40-48 GB | A100 40GB, A6000 | ~25 tok/s |

### Recommended Configurations

**Minimal (Small Team, Light Usage):**
```
1x NVIDIA A10 (24GB)
- Llama 3.1 8B (primary)
- Llama 3.2 3B (fast tasks)
- nomic-embed-text (embeddings)
```

**Standard (Enterprise, Medium Usage):**
```
2x NVIDIA A100 40GB
- Llama 3.1 70B (quantized, primary)
- Mistral 7B (fast tasks)
- Embeddings model
```

**High-Performance (Heavy Usage, Large Teams):**
```
4x NVIDIA H100 80GB
- Llama 3.1 70B (full precision)
- Multiple model instances
- High concurrency
```

---

## Security Considerations

| Aspect | Cloud | On-Premise | Air-Gapped |
|--------|-------|------------|------------|
| **Data Residency** | Provider's servers | Your datacenter | Your isolated network |
| **Encryption in Transit** | TLS (provider) | TLS (internal CA) | Optional (no egress) |
| **API Keys** | Secret Manager | Vault / K8s Secrets | Local config |
| **Audit Logging** | Provider logs | Full control | Full control |
| **Model Integrity** | Trust provider | Verify checksums | Verify + sign |
| **PII Handling** | Check provider DPA | Your policy | Your policy |

---

## Configuration

```yaml
# config/llm.yaml

deployment_mode: on_premise  # cloud | on_premise | air_gapped

providers:
  anthropic:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-sonnet-4-20250514
    
  ollama:
    enabled: true
    base_url: http://gpu-server:11434
    models:
      large: llama3.1:70b
      small: llama3.2:3b
      embed: nomic-embed-text
      code: codellama:34b

task_routing:
  intent_classification: ollama:small
  slot_filling: ollama:small
  deck_generation: ollama:large
  explanation: ollama:large
  embedding: ollama:embed
  code_generation: ollama:code

fallback:
  enabled: true
  allow_cloud: false  # Air-gapped: no cloud fallback
  
vector_store:
  provider: qdrant
  url: http://qdrant:6333
  collection: clarissa_docs
```

---

## Summary

| Decision | Choice |
|----------|--------|
| **Abstraction** | LLMInterface + Provider Adapters |
| **Routing** | Task-based ModelRouter |
| **Cloud** | Anthropic (primary), OpenAI (fallback) |
| **On-Premise** | Ollama / vLLM with Llama 3.1 |
| **Air-Gapped** | Ollama + local models only |
| **Embeddings** | nomic-embed-text (local) / text-embedding-3 (cloud) |
| **Vector Store** | Qdrant (on-prem) / Chroma (air-gapped) |
| **Fallback** | Configurable per deployment mode |

---

## References

- [ADR-024: CLARISSA Core System Architecture](./ADR-024-clarissa-core-system-architecture.md)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Ollama](https://ollama.ai/)
- [vLLM](https://docs.vllm.ai/)
- [Llama 3.1 Model Card](https://ai.meta.com/llama/)
- [Qdrant Vector Database](https://qdrant.tech/)