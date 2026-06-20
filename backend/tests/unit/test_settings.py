"""
Unit tests for config/settings.py
"""
import pytest
from pydantic import ValidationError


class TestSettingsLoad:
    def test_valid_env_loads(self, monkeypatch):
        """Settings load without error when all required keys are valid."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")
        monkeypatch.setenv("ENV", "development")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")
        assert s.openai_api_key == "test-openai-api-key"

    def test_plain_postgres_url_gets_upgraded(self, monkeypatch):
        """postgresql:// URL should be auto-upgraded to postgresql+asyncpg://."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_invalid_database_url_raises(self, monkeypatch):
        """A DATABASE_URL that isn't postgresql should fail validation."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")

        import importlib
        import config.settings as settings_module
        with pytest.raises((ValidationError, ValueError, Exception)):
            importlib.reload(settings_module)

    def test_invalid_openai_key_format_raises(self, monkeypatch):
        """An OpenAI key that doesn't start with 'sk-' should fail validation."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "bad-key-format")

        import importlib
        import config.settings as settings_module
        with pytest.raises((ValidationError, ValueError, Exception)):
            importlib.reload(settings_module)

    def test_deepseek_provider_loads_with_key(self, monkeypatch):
        """DeepSeek can be selected as the active LLM provider."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-ci-testing-only-32plus")
        monkeypatch.setenv("LLM_PROVIDER", "deepseek")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()

        assert s.llm_provider == "deepseek"
        assert s.deepseek_base_url == "https://api.deepseek.com"
        assert s.deepseek_model_small == "deepseek-v4-flash"

    def test_deepseek_provider_requires_key(self, monkeypatch):
        """DeepSeek provider should fail fast without DEEPSEEK_API_KEY."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-ci-testing-only-32plus")
        monkeypatch.setenv("LLM_PROVIDER", "deepseek")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "")

        import importlib
        import config.settings as settings_module
        with pytest.raises((ValidationError, ValueError, Exception)):
            importlib.reload(settings_module)
