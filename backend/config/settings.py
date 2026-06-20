"""
Option Oracle — Application Configuration

All settings are loaded from environment variables (or a .env file).
Invalid / missing required values raise ValidationError on startup —
the application will refuse to start rather than silently misconfigure.
"""
from typing import List, Literal, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Required fields raise ValidationError if absent or malformed.
    Optional fields default to sensible values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str  # required — set DATABASE_URL env var
    redis_url: Optional[str] = None

    # ------------------------------------------------------------------
    # Auth / JWT
    # ------------------------------------------------------------------
    jwt_secret_key: str  # required — set JWT_SECRET_KEY env var (min 32 chars)
    admin_api_token: Optional[str] = None
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # ------------------------------------------------------------------
    # LLM Provider Selection
    # Switch between providers by setting LLM_PROVIDER in .env
    # ------------------------------------------------------------------
    llm_provider: Literal["openai", "gemini", "deepseek"] = "openai"

    # OpenAI — required when llm_provider="openai"
    openai_api_key: Optional[str] = None
    openai_model_large: str = "gpt-4o"
    openai_model_small: str = "gpt-4o-mini"

    # Gemini — required when llm_provider="gemini"
    gemini_api_key: Optional[str] = None
    gemini_model_large: str = "gemini-2.0-flash"
    gemini_model_small: str = "gemini-2.0-flash-lite"

    # DeepSeek — required when llm_provider="deepseek"
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model_large: str = "deepseek-v4-pro"
    deepseek_model_small: str = "deepseek-v4-flash"

    # ------------------------------------------------------------------
    # Optional external APIs
    # ------------------------------------------------------------------
    jigsawstack_api_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    stocktwits_access_token: Optional[str] = None
    news_api_key: Optional[str] = None

    # ------------------------------------------------------------------
    # Optional ingestion layer, ported from Sajan architecture
    # ------------------------------------------------------------------
    ingestion_kafka_enabled: bool = False
    ingestion_dask_enabled: bool = False
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_consumer_group: str = "option-oracle"
    dask_scheduler_address: str = "tcp://dask-scheduler:8786"
    dask_n_workers: int = 2

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ------------------------------------------------------------------
    # Timeouts
    # ------------------------------------------------------------------
    openai_timeout_seconds: int = 30
    db_connect_timeout: int = 10
    analysis_timeout_seconds: int = 30

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 200

    # ------------------------------------------------------------------
    # Trading / system
    # ------------------------------------------------------------------
    max_concurrent_analysis: int = 10
    default_risk_profile: str = "moderate"
    paper_trading_balance: float = 100_000.0
    live_trading_enabled: bool = False

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_postgresql(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+asyncpg://' or 'postgresql://'. "
                "Example: postgresql+asyncpg://user@localhost:5432/option_oracle"
            )
        return v

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def validate_openai_key_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith("sk-") or v.startswith("test-")):
            raise ValueError(
                "OPENAI_API_KEY must start with 'sk-' or use a 'test-' placeholder. "
                "Get your key from https://platform.openai.com/api-keys"
            )
        return v or None

    @field_validator("app_port")
    @classmethod
    def port_must_be_in_valid_range(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError(f"APP_PORT must be between 1024 and 65535, got: {v}")
        return v

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> "Settings":
        """Ensure the selected provider has its API key set."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
                "Set it in your .env file or switch to LLM_PROVIDER=gemini."
            )
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
                "Get your key from https://aistudio.google.com/app/apikey"
            )
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek. "
                "Get your key from https://platform.deepseek.com/api_keys"
            )
        return self


# ---------------------------------------------------------------------------
# Global singleton — imported everywhere as `from config.settings import settings`
# ---------------------------------------------------------------------------
settings = Settings()
