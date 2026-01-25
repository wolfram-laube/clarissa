"""
CLARISSA LLM Provider Abstraction

Multi-provider LLM support with automatic fallback.
Supports: OpenAI, Anthropic, Ollama (local)

Usage:
    from clarissa.api.llm import get_llm_response
    
    response = await get_llm_response(
        message="Help me create a waterflood model",
        conversation_history=[...]
    )

Configuration via environment:
    LLM_PROVIDER=openai          # Primary provider
    LLM_FALLBACK_ENABLED=true    # Enable fallback on errors
    LLM_FALLBACK_ORDER=anthropic,ollama  # Fallback order
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

import httpx

from clarissa.config import settings

logger = logging.getLogger(__name__)


# ============== Data Classes ==============
@dataclass
class Message:
    """Chat message."""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    content: str
    provider: str
    model: str
    usage: dict | None = None
    fallback_used: bool = False


# ============== Provider Exceptions ==============
class LLMError(Exception):
    """Base LLM error."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded - should trigger fallback."""
    pass


class LLMAuthError(LLMError):
    """Authentication failed - API key issue."""
    pass


class LLMUnavailableError(LLMError):
    """Provider unavailable - should trigger fallback."""
    pass


# ============== Base Provider ==============
class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str = "base"
    
    @abstractmethod
    async def chat(
        self, 
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send chat request to LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


# ============== OpenAI Provider ==============
class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    name = "openai"
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self._client = None
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.api_key != "not-configured"
    
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if not self.is_available():
            raise LLMAuthError("OpenAI API key not configured")
        
        from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError
        
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        
        # Build messages list
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=self.name,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
            )
        
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit: {e}")
            raise LLMRateLimitError(str(e))
        except AuthenticationError as e:
            logger.error(f"OpenAI auth error: {e}")
            raise LLMAuthError(str(e))
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMUnavailableError(str(e))


# ============== Anthropic Provider ==============
class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    name = "anthropic"
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self._client = None
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.api_key != "not-configured"
    
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if not self.is_available():
            raise LLMAuthError("Anthropic API key not configured")
        
        from anthropic import AsyncAnthropic, APIError, RateLimitError, AuthenticationError
        
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        
        # Build messages list (Anthropic format)
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            kwargs = {
                "model": self.model,
                "messages": api_messages,
                "max_tokens": max_tokens,
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self._client.messages.create(**kwargs)
            
            return LLMResponse(
                content=response.content[0].text,
                provider=self.name,
                model=self.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
            )
        
        except RateLimitError as e:
            logger.warning(f"Anthropic rate limit: {e}")
            raise LLMRateLimitError(str(e))
        except AuthenticationError as e:
            logger.error(f"Anthropic auth error: {e}")
            raise LLMAuthError(str(e))
        except APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMUnavailableError(str(e))


# ============== Ollama Provider ==============
class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    name = "ollama"
    
    def __init__(self):
        self.host = settings.ollama_host
        self.model = settings.ollama_model
    
    def is_available(self) -> bool:
        # Check if Ollama is reachable
        try:
            import httpx
            response = httpx.get(f"{self.host}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            # Build messages
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                api_messages.append({"role": msg.role, "content": msg.content})
            
            try:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                data = response.json()
                
                return LLMResponse(
                    content=data["message"]["content"],
                    provider=self.name,
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                )
            
            except httpx.ConnectError as e:
                logger.error(f"Ollama connection error: {e}")
                raise LLMUnavailableError(f"Ollama unavailable at {self.host}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e}")
                raise LLMUnavailableError(str(e))


# ============== Provider Manager ==============
class LLMProviderManager:
    """
    Manages LLM providers with automatic fallback.
    
    Fallback order (configurable):
    1. Primary provider (from settings.llm_provider)
    2. Secondary providers in order
    """
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    
    # Default fallback order (cost-optimized: OpenAI first)
    DEFAULT_FALLBACK_ORDER = ["openai", "anthropic", "ollama"]
    
    def __init__(self):
        self.primary = settings.llm_provider
        self._providers: dict[str, BaseLLMProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers."""
        for name, cls in self.PROVIDERS.items():
            provider = cls()
            if provider.is_available():
                self._providers[name] = provider
                logger.info(f"LLM provider available: {name}")
            else:
                logger.debug(f"LLM provider not configured: {name}")
    
    def get_fallback_order(self) -> list[str]:
        """Get fallback order starting with primary."""
        order = [self.primary]
        for provider in self.DEFAULT_FALLBACK_ORDER:
            if provider != self.primary and provider in self._providers:
                order.append(provider)
        return order
    
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        enable_fallback: bool = True,
    ) -> LLMResponse:
        """
        Send chat request with automatic fallback.
        
        Args:
            messages: Conversation messages
            system_prompt: System prompt for context
            temperature: Creativity (0.0-1.0)
            max_tokens: Max response tokens
            enable_fallback: Try other providers on failure
            
        Returns:
            LLMResponse with content and metadata
        """
        fallback_order = self.get_fallback_order()
        last_error: Exception | None = None
        
        for i, provider_name in enumerate(fallback_order):
            if provider_name not in self._providers:
                continue
            
            provider = self._providers[provider_name]
            is_fallback = i > 0
            
            try:
                logger.info(f"Trying LLM provider: {provider_name}" + 
                          (" (fallback)" if is_fallback else " (primary)"))
                
                response = await provider.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                response.fallback_used = is_fallback
                
                if is_fallback:
                    logger.info(f"Fallback to {provider_name} successful")
                
                return response
            
            except (LLMRateLimitError, LLMUnavailableError) as e:
                last_error = e
                if enable_fallback:
                    logger.warning(f"{provider_name} failed: {e}, trying fallback...")
                    continue
                raise
            
            except LLMAuthError as e:
                last_error = e
                logger.error(f"{provider_name} auth error: {e}")
                if enable_fallback:
                    continue
                raise
        
        # All providers failed
        raise LLMError(f"All LLM providers failed. Last error: {last_error}")


# ============== Module-level Instance ==============
_manager: LLMProviderManager | None = None


def get_manager() -> LLMProviderManager:
    """Get or create the provider manager singleton."""
    global _manager
    if _manager is None:
        _manager = LLMProviderManager()
    return _manager


# ============== Convenience Functions ==============
async def get_llm_response(
    message: str,
    conversation_history: list[dict] | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> LLMResponse:
    """
    High-level function to get LLM response.
    
    Args:
        message: User message
        conversation_history: Previous messages [{"role": "user/assistant", "content": "..."}]
        system_prompt: System context
        temperature: Creativity level
        max_tokens: Max response length
        
    Returns:
        LLMResponse with content, provider info, and usage stats
    """
    manager = get_manager()
    
    # Build message list
    messages = []
    if conversation_history:
        for msg in conversation_history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
    messages.append(Message(role="user", content=message))
    
    # Default system prompt for CLARISSA
    if system_prompt is None:
        system_prompt = """You are CLARISSA (Conversational Language Agent for Reservoir Integrated 
Simulation System Analysis), an AI assistant specialized in reservoir engineering and simulation.

You help reservoir engineers:
- Build and modify simulation input decks (Eclipse format)
- Understand simulation parameters and keywords
- Analyze simulation results
- Suggest optimizations for field development plans

Be concise, technically accurate, and helpful. When generating deck content, 
use proper Eclipse keyword syntax."""
    
    return await manager.chat(
        messages=messages,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
