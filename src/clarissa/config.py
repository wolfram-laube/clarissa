"""
CLARISSA Configuration Module

Handles environment-based configuration with sensible defaults for local development.
Uses pydantic-settings for type-safe configuration loading.

Usage:
    from clarissa.config import settings
    
    if settings.is_local:
        # Local development behavior
    
    llm = get_llm_client()  # Automatically uses correct provider
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with local-first defaults.
    
    All settings can be overridden via environment variables.
    For local development, defaults work out of the box with docker-compose.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ============== Environment ==============
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
    debug: bool = True
    
    # ============== API ==============
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # ============== LLM Configuration ==============
    llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama"
    
    # Ollama (local LLM)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    
    # Anthropic Claude
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    
    # ============== Database ==============
    firestore_emulator_host: str | None = "localhost:8080"
    firestore_project: str = "myk8sproject-207017"
    
    # ============== Simulator ==============
    opm_flow_url: str = "http://localhost:5000"
    simulation_timeout: int = 3600  # 1 hour default
    
    # ============== Vector Store ==============
    qdrant_host: str = "http://localhost:6333"
    qdrant_collection: str = "clarissa_docs"
    
    # ============== Computed Properties ==============
    @property
    def is_local(self) -> bool:
        """Check if running in local development mode."""
        return self.environment == "local"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "prod"
    
    @property
    def use_firestore_emulator(self) -> bool:
        """Check if Firestore emulator should be used."""
        return bool(self.firestore_emulator_host)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience export
settings = get_settings()
