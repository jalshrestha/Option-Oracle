"""
Option Oracle — Application Configuration

All settings are loaded from environment variables (or a .env file).
Invalid / missing required values raise ValidationError on startup —
the application will refuse to start rather than silently misconfigure.
"""
from typing import List, Literal, Optional

from pydantic import field_validator
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
    # Required — application refuses to start without these
    # ------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://oracle:oracle_dev@postgres:5432/option_oracle"
    openai_api_key: str

    # ------------------------------------------------------------------
    # Optional — reduced functionality when absent
    # ------------------------------------------------------------------
    gemini_api_key: Optional[str] = None
    jigsawstack_api_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    stocktwits_access_token: Optional[str] = None
    news_api_key: Optional[str] = None

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

    # ------------------------------------------------------------------
    # Validators — fail fast with clear messages
    # ------------------------------------------------------------------

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_postgresql(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            # Auto-upgrade to asyncpg driver
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+asyncpg://' or 'postgresql://'. "
                "Example: postgresql+asyncpg://user:pass@localhost:5432/option_oracle"
            )
        return v

    @field_validator("openai_api_key")
    @classmethod
    def openai_key_must_start_with_sk(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError(
                "OPENAI_API_KEY must start with 'sk-'. "
                "Get your key from https://platform.openai.com/api-keys"
            )
        return v

    @field_validator("app_port")
    @classmethod
    def port_must_be_in_valid_range(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError(
                f"APP_PORT must be between 1024 and 65535, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# Global singleton — imported everywhere as `from config.settings import settings`
# ---------------------------------------------------------------------------
settings = Settings()
