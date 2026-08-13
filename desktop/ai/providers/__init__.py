from __future__ import annotations

from desktop.ai.config import AIClientConfig, normalize_provider
from desktop.ai.providers.anthropic import AnthropicProviderAdapter
from desktop.ai.providers.base import BaseAIProviderAdapter
from desktop.ai.providers.openai import OpenAIProviderAdapter
from desktop.ai.providers.openai_chat import OpenAIChatProviderAdapter
from desktop.ai.transport import Transport


def get_provider_adapter(config: AIClientConfig, transport: Transport) -> BaseAIProviderAdapter:
    """Return the strategy adapter matching the configured AI provider."""
    provider = normalize_provider(config.provider)
    if provider == "openai":
        return OpenAIProviderAdapter(config, transport)
    if provider == "anthropic":
        return AnthropicProviderAdapter(config, transport)
    # Default to OpenAIChatProviderAdapter for openrouter, groq, tokenrouter, nvidia, and ANY custom OpenAI-compatible provider!
    return OpenAIChatProviderAdapter(config, transport)


__all__ = [
    "AnthropicProviderAdapter",
    "BaseAIProviderAdapter",
    "OpenAIChatProviderAdapter",
    "OpenAIProviderAdapter",
    "get_provider_adapter",
]
