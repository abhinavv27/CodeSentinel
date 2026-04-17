from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "CodeSentinel"
    debug: bool = False
    otlp_endpoint: str = ""  # e.g., "http://jaeger:4317"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/codesentinel"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GitHub
    github_webhook_secret: str = ""
    github_app_private_key: str = ""
    github_app_id: int = 0

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    
    # Notifications
    slack_webhook_url: str = ""
    qdrant_collection: str = "codebase"
    qdrant_feedback_collection: str = "feedback_memory"

    # Model (vLLM / Ollama OpenAI-compat endpoint)
    model_endpoint: str = "http://localhost:11434/v1"
    model_name: str = "codellama:7b"
    model_max_tokens: int = 2048

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Review settings
    confidence_threshold: float = 0.6


@lru_cache
def get_settings() -> Settings:
    return Settings()
