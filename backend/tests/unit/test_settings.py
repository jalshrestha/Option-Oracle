"""
Unit tests for config/settings.py
"""
import pytest
from pydantic import ValidationError


class TestSettingsLoad:
    def test_valid_env_loads(self, monkeypatch):
        """Settings load without error when all required keys are valid."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-1234567890")
        monkeypatch.setenv("ENV", "development")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")
        assert s.openai_api_key.startswith("sk-")

    def test_plain_postgres_url_gets_upgraded(self, monkeypatch):
        """postgresql:// URL should be auto-upgraded to postgresql+asyncpg://."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_invalid_database_url_raises(self, monkeypatch):
        """A DATABASE_URL that isn't postgresql should fail validation."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)

        with pytest.raises((ValidationError, ValueError, Exception)):
            settings_module.Settings()

    def test_invalid_openai_key_format_raises(self, monkeypatch):
        """An OpenAI key that doesn't start with 'sk-' should fail validation."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("OPENAI_API_KEY", "bad-key-format")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)

        with pytest.raises((ValidationError, ValueError, Exception)):
            settings_module.Settings()
