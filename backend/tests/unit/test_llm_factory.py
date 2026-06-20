"""Unit tests for the LLM provider factory."""


def test_create_deepseek_client(monkeypatch):
    """Factory should return the DeepSeek client when provider is deepseek."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-ci-testing-only-32plus")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")

    import importlib
    import config.settings as settings_module
    import src.llm.factory as factory_module

    importlib.reload(settings_module)
    importlib.reload(factory_module)

    client = factory_module.create_llm_client("small")

    assert client.provider == "deepseek"
    assert client.model_name == "deepseek-v4-flash"


def test_create_deepseek_large_client(monkeypatch):
    """Factory should use the configured large DeepSeek model for complex tasks."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-ci-testing-only-32plus")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setenv("DEEPSEEK_MODEL_LARGE", "deepseek-v4-pro")

    import importlib
    import config.settings as settings_module
    import src.llm.factory as factory_module

    importlib.reload(settings_module)
    importlib.reload(factory_module)

    client = factory_module.create_llm_client("large", provider="deepseek")

    assert client.provider == "deepseek"
    assert client.model_name == "deepseek-v4-pro"
