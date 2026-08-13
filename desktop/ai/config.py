from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from desktop.ai.exceptions import AIClientError

AIProvider = str
AI_PROVIDERS: tuple[str, ...] = (
    "openai",
    "anthropic",
    "openrouter",
    "groq",
    "tokenrouter",
    "nvidia",
)
AI_PROVIDER_ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "tokenrouter": "TOKENROUTER_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
}
AI_PROVIDER_BASE_URL_ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_BASE_URL",
    "anthropic": "ANTHROPIC_BASE_URL",
    "openrouter": "OPENROUTER_BASE_URL",
    "groq": "GROQ_BASE_URL",
    "tokenrouter": "TOKENROUTER_BASE_URL",
    "nvidia": "NVIDIA_BASE_URL",
}
OPENAI_COMPATIBLE_CHAT_ENDPOINTS: tuple[str, ...] = (
    "openrouter",
    "groq",
    "tokenrouter",
    "nvidia",
)
AI_PROVIDER_ALIASES: dict[str, str] = {
    "qroq": "groq",
    "nvidia-nim": "nvidia",
    "nvidia_nim": "nvidia",
}


@dataclass(frozen=True, slots=True)
class AIClientConfig:
    provider: str = "groq"
    api_key: str | None = None
    model: str | None = None
    timeout_s: float = 30.0
    max_output_tokens: int = 800

    def __post_init__(self) -> None:
        normalize_provider(self.provider)
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")

    @classmethod
    def from_env(cls, provider: str | None = None) -> AIClientConfig:
        selected_provider = normalize_provider(provider or os.getenv("RTDA_AI_PROVIDER", "groq"))
        api_key = os.getenv(env_var_for_provider(selected_provider))
        return cls(
            provider=selected_provider,
            api_key=api_key,
            model=default_model(selected_provider),
        )

    def resolved_model(self) -> str:
        return self.model or default_model(self.provider)

    def resolved_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        env_name = env_var_for_provider(self.provider)
        env_value = os.getenv(env_name)
        if env_value:
            return env_value
        base_url_env = base_url_env_var_for_provider(self.provider)
        if os.getenv(base_url_env):
            return "not-needed"
        raise AIClientError(
            f"missing API token for provider '{self.provider}'. "
            f"Paste it in the desktop Token field or set {env_name} before starting RTDA."
        )

    def resolved_base_url(self) -> str:
        return base_url_for_provider(self.provider)


def default_model(provider: str) -> str:
    provider = normalize_provider(provider)
    if provider == "openai":
        return "gpt-5.6-terra"
    if provider == "anthropic":
        return "claude-sonnet-5"
    if provider == "openrouter":
        return "openrouter/free"
    if provider == "groq":
        return "llama-3.3-70b-versatile"
    if provider == "tokenrouter":
        return "moonshotai/kimi-k3-free"
    if provider == "nvidia":
        return "meta/llama-3.3-70b-instruct"
    return os.getenv(f"{provider.upper()}_MODEL", "default-model")


def normalize_provider(provider: str) -> str:
    selected = provider.strip().lower()
    if selected in AI_PROVIDER_ALIASES:
        return AI_PROVIDER_ALIASES[selected]
    return selected


def env_var_for_provider(provider: str) -> str:
    normalized = normalize_provider(provider)
    if normalized in AI_PROVIDER_ENV_VARS:
        return AI_PROVIDER_ENV_VARS[normalized]
    return f"{normalized.upper()}_API_KEY"


def base_url_env_var_for_provider(provider: str) -> str:
    normalized = normalize_provider(provider)
    if normalized in AI_PROVIDER_BASE_URL_ENV_VARS:
        return AI_PROVIDER_BASE_URL_ENV_VARS[normalized]
    return f"{normalized.upper()}_BASE_URL"


def base_url_for_provider(provider: str) -> str:
    normalized = normalize_provider(provider)
    env_var = base_url_env_var_for_provider(normalized)
    url = os.getenv(env_var, "").strip()
    if not url:
        raise AIClientError(
            f"missing Base URL for provider '{provider}'. "
            f"Set {env_var} in your .env file before starting RTDA."
        )
    return url.rstrip("/")


def _endpoint_for_provider(provider: str, default_path: str) -> str:
    base = base_url_for_provider(provider)
    if base.endswith(default_path):
        return base
    return f"{base}{default_path}"


def _chat_endpoint_for_provider(provider: str) -> str:
    return _endpoint_for_provider(provider, "/chat/completions")
