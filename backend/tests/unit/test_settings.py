"""
Unit tests for config/settings.py
"""
import pytest
from pydantic import ValidationError


class TestSettingsLoad:
    def test_valid_env_loads(self, monkeypatch):
        """Settings load without error when all required keys are valid."""
        monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-1234567890")
        monkeypatch.setenv("ENV", "development")

        # Re-import to pick up monkeypatched env
        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)
        s = settings_module.Settings()
        assert s.supabase_url.startswith("https://")
        assert s.openai_api_key.startswith("sk-")

    def test_missing_supabase_url_raises(self, monkeypatch):
        """Missing SUPABASE_URL should raise ValidationError at startup."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "some-key")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("ENV", "development")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)

        with pytest.raises((ValidationError, Exception)):
            settings_module.Settings()

    def test_invalid_openai_key_format_raises(self, monkeypatch):
        """An OpenAI key that doesn't start with 'sk-' should fail validation."""
        monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "some-service-key")
        monkeypatch.setenv("OPENAI_API_KEY", "bad-key-format")
        monkeypatch.setenv("ENV", "development")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)

        with pytest.raises((ValidationError, ValueError, Exception)):
            settings_module.Settings()

    def test_invalid_supabase_url_not_https_raises(self, monkeypatch):
        """A Supabase URL without https:// should fail validation."""
        monkeypatch.setenv("SUPABASE_URL", "http://insecure.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "some-service-key")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("ENV", "development")

        import importlib
        import config.settings as settings_module
        importlib.reload(settings_module)

        with pytest.raises((ValidationError, ValueError, Exception)):
            settings_module.Settings()
