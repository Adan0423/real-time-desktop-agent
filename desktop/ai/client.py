from __future__ import annotations

from desktop.ai.config import (
    AI_PROVIDER_ALIASES,
    AI_PROVIDER_BASE_URL_ENV_VARS,
    AI_PROVIDER_ENV_VARS,
    AI_PROVIDERS,
    OPENAI_COMPATIBLE_CHAT_ENDPOINTS,
    AIClientConfig,
    AIProvider,
    base_url_for_provider,
    default_model,
    env_var_for_provider,
    normalize_provider,
)
from desktop.ai.exceptions import AIClientError
from desktop.ai.models import AIResponse
from desktop.ai.providers import get_provider_adapter
from desktop.ai.transport import Transport, post_json


class AIClient:
    """Main facade orchestrator for AI completions, delegating to provider strategies."""

    def __init__(self, config: AIClientConfig, *, transport: Transport | None = None) -> None:
        self.config = config
        self._transport = transport or post_json

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image_data_url: str | None = None,
    ) -> AIResponse:
        prompt = prompt.strip()
        if not prompt:
            raise AIClientError("prompt is empty")

        adapter = get_provider_adapter(self.config, self._transport)
        return adapter.complete(prompt, system=system, image_data_url=image_data_url)


__all__ = [
    "AI_PROVIDERS",
    "AI_PROVIDER_ALIASES",
    "AI_PROVIDER_BASE_URL_ENV_VARS",
    "AI_PROVIDER_ENV_VARS",
    "OPENAI_COMPATIBLE_CHAT_ENDPOINTS",
    "AIClient",
    "AIClientConfig",
    "AIClientError",
    "AIProvider",
    "AIResponse",
    "Transport",
    "base_url_for_provider",
    "default_model",
    "env_var_for_provider",
    "normalize_provider",
]
