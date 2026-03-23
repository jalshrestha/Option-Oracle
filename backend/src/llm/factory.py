"""
LLM Client Factory.

Usage:
    from src.llm.factory import create_llm_client

    client = create_llm_client("large")   # uses settings.llm_provider
    client = create_llm_client("small")   # cost-optimized model
    client = create_llm_client("large", provider="gemini")  # explicit override
"""
from typing import Optional

from src.llm.base import LLMClient


def create_llm_client(
    model_size: str = "large",
    provider: Optional[str] = None,
) -> LLMClient:
    """
    Create an LLMClient for the configured or specified provider.

    Args:
        model_size: "large" for complex analysis (gpt-4o / gemini-2.0-flash)
                    "small" for cost-optimized tasks (gpt-4o-mini / gemini-2.0-flash-lite)
        provider:   Override the provider from settings ("openai" or "gemini").
                    Defaults to settings.llm_provider.

    Returns:
        An LLMClient implementation ready for async use.

    Raises:
        ValueError: If provider is unknown or required API key is missing.
    """
    from config.settings import settings  # late import — avoids circular dep at module load

    resolved_provider = provider or settings.llm_provider

    if resolved_provider == "openai":
        from src.llm.openai_client import OpenAILLMClient
        model = (
            settings.openai_model_large if model_size == "large"
            else settings.openai_model_small
        )
        return OpenAILLMClient(api_key=settings.openai_api_key, model=model)

    elif resolved_provider == "gemini":
        from src.llm.gemini_client import GeminiLLMClient
        model = (
            settings.gemini_model_large if model_size == "large"
            else settings.gemini_model_small
        )
        return GeminiLLMClient(api_key=settings.gemini_api_key, model=model)

    else:
        raise ValueError(
            f"Unknown LLM provider: '{resolved_provider}'. "
            "Set LLM_PROVIDER=openai or LLM_PROVIDER=gemini in your .env"
        )
