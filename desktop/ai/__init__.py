from __future__ import annotations

from desktop.ai.client import (
    AI_PROVIDERS,
    AI_PROVIDER_ALIASES,
    AI_PROVIDER_BASE_URL_ENV_VARS,
    AI_PROVIDER_ENV_VARS,
    OPENAI_COMPATIBLE_CHAT_ENDPOINTS,
    AIClient,
    AIClientConfig,
    AIClientError,
    AIProvider,
    AIResponse,
    base_url_for_provider,
    default_model,
    env_var_for_provider,
    normalize_provider,
)

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
    "base_url_for_provider",
    "default_model",
    "env_var_for_provider",
    "normalize_provider",
]
