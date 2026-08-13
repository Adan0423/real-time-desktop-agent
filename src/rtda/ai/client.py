from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

AIProvider = Literal["openai", "anthropic", "openrouter", "groq", "tokenrouter", "nvidia"]
Transport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]
AI_PROVIDERS: tuple[AIProvider, ...] = (
    "openai",
    "anthropic",
    "openrouter",
    "groq",
    "tokenrouter",
    "nvidia",
)
AI_PROVIDER_ENV_VARS: dict[AIProvider, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "tokenrouter": "TOKENROUTER_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
}
AI_PROVIDER_ALIASES: dict[str, AIProvider] = {
    "qroq": "groq",
    "nvidia-nim": "nvidia",
    "nvidia_nim": "nvidia",
}
OPENAI_COMPATIBLE_CHAT_ENDPOINTS: dict[AIProvider, str] = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "tokenrouter": "https://api.tokenrouter.com/v1/chat/completions",
    "nvidia": "https://integrate.api.nvidia.com/v1/chat/completions",
}


class AIClientError(RuntimeError):
    """Raised when an AI provider request cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class AIClientConfig:
    provider: AIProvider = "groq"
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
    def from_env(cls, provider: AIProvider | None = None) -> "AIClientConfig":
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
        raise AIClientError(
            f"missing API token for provider '{self.provider}'. "
            f"Paste it in the desktop Token field or set {env_name} before starting RTDA."
        )


@dataclass(frozen=True, slots=True)
class AIResponse:
    provider: AIProvider
    model: str
    output_text: str
    raw: Mapping[str, Any]


def default_model(provider: AIProvider) -> str:
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
    raise ValueError("unsupported provider")


class AIClient:
    def __init__(self, config: AIClientConfig, *, transport: Transport | None = None) -> None:
        self.config = config
        self._transport = transport or _post_json

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
        if self.config.provider == "openai":
            return self._complete_openai(prompt, system=system, image_data_url=image_data_url)
        if self.config.provider == "anthropic":
            return self._complete_anthropic(prompt, system=system, image_data_url=image_data_url)
        if self.config.provider in OPENAI_COMPATIBLE_CHAT_ENDPOINTS:
            return self._complete_openai_compatible_chat(prompt, system=system, image_data_url=image_data_url)
        raise AIClientError(f"unsupported provider: {self.config.provider}")

    def _complete_openai(self, prompt: str, *, system: str | None, image_data_url: str | None) -> AIResponse:
        model = self.config.resolved_model()
        payload: dict[str, Any] = {
            "model": model,
            "input": prompt,
            "store": False,
            "max_output_tokens": self.config.max_output_tokens,
        }
        if system:
            payload["instructions"] = system
        if image_data_url:
            payload["input"] = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                }
            ]
        raw = self._transport(
            "https://api.openai.com/v1/responses",
            {
                "Authorization": f"Bearer {self.config.resolved_api_key()}",
                "Content-Type": "application/json",
            },
            payload,
            self.config.timeout_s,
        )
        return AIResponse(
            provider="openai",
            model=model,
            output_text=_extract_openai_text(raw),
            raw=raw,
        )

    def _complete_anthropic(self, prompt: str, *, system: str | None, image_data_url: str | None) -> AIResponse:
        model = self.config.resolved_model()
        message_content: str | list[dict[str, Any]] = prompt
        if image_data_url:
            media_type, data = _parse_data_url(image_data_url)
            message_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                },
            ]
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.config.max_output_tokens,
            "messages": [{"role": "user", "content": message_content}],
        }
        if system:
            payload["system"] = system
        raw = self._transport(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": self.config.resolved_api_key(),
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            payload,
            self.config.timeout_s,
        )
        return AIResponse(
            provider="anthropic",
            model=model,
            output_text=_extract_anthropic_text(raw),
            raw=raw,
        )

    def _complete_openai_compatible_chat(
        self,
        prompt: str,
        *,
        system: str | None,
        image_data_url: str | None,
    ) -> AIResponse:
        provider = normalize_provider(self.config.provider)
        model = self.config.resolved_model()
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        user_content: str | list[dict[str, Any]] = prompt
        if image_data_url:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]
        messages.append({"role": "user", "content": user_content})
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": self.config.max_output_tokens,
            "stream": False,
        }
        raw = self._transport(
            _chat_endpoint_for_provider(provider),
            _headers_for_chat_provider(provider, self.config.resolved_api_key()),
            payload,
            self.config.timeout_s,
        )
        return AIResponse(
            provider=provider,
            model=model,
            output_text=_extract_chat_completion_text(raw),
            raw=raw,
        )


def normalize_provider(provider: str) -> AIProvider:
    selected = provider.strip().lower()
    if selected in AI_PROVIDER_ALIASES:
        return AI_PROVIDER_ALIASES[selected]
    if selected in AI_PROVIDERS:
        return selected  # type: ignore[return-value]
    allowed = ", ".join(AI_PROVIDERS)
    raise ValueError(f"AI provider must be one of: {allowed}")


def env_var_for_provider(provider: AIProvider) -> str:
    return AI_PROVIDER_ENV_VARS[normalize_provider(provider)]


def _chat_endpoint_for_provider(provider: AIProvider) -> str:
    if provider == "tokenrouter":
        base_url = os.getenv("TOKENROUTER_BASE_URL", "").strip()
        if base_url:
            clean = base_url.rstrip("/")
            if clean.endswith("/chat/completions"):
                return clean
            return f"{clean}/chat/completions"
    return OPENAI_COMPATIBLE_CHAT_ENDPOINTS[provider]


def _headers_for_chat_provider(provider: AIProvider, api_key: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/Adan0423/real-time-desktop-agent"
        headers["X-OpenRouter-Title"] = "Real-Time Desktop Agent"
    if provider == "nvidia":
        headers["Accept"] = "application/json"
    return headers


def _post_json(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout_s: float,
) -> Mapping[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AIClientError(f"AI provider returned HTTP {exc.code}: {_safe_error_body(body)}") from exc
    except urllib.error.URLError as exc:
        raise AIClientError(f"AI provider request failed: {exc.reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AIClientError(f"AI provider request timed out after {timeout_s:.0f}s") from exc
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AIClientError("AI provider returned invalid JSON") from exc
    if not isinstance(decoded, Mapping):
        raise AIClientError("AI provider returned a non-object JSON payload")
    return decoded


def _safe_error_body(body: str) -> str:
    compact = " ".join(body.split())
    return compact[:300]


def _parse_data_url(data_url: str) -> tuple[str, str]:
    prefix, separator, data = data_url.partition(",")
    if not separator or not prefix.startswith("data:") or ";base64" not in prefix:
        raise AIClientError("image payload must be a base64 data URL")
    media_type = prefix.removeprefix("data:").split(";", 1)[0]
    return media_type, data


def _extract_openai_text(raw: Mapping[str, Any]) -> str:
    direct = raw.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    parts: list[str] = []
    output = raw.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, Mapping):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, Mapping):
                        text = block.get("text")
                        if isinstance(text, str):
                            parts.append(text)
    text = "\n".join(part.strip() for part in parts if part.strip())
    if text:
        return text
    raise AIClientError("OpenAI response did not include text output")


def _extract_anthropic_text(raw: Mapping[str, Any]) -> str:
    parts: list[str] = []
    content = raw.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, Mapping) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
    text = "\n".join(part.strip() for part in parts if part.strip())
    if text:
        return text
    raise AIClientError("Anthropic response did not include text output")


def _extract_chat_completion_text(raw: Mapping[str, Any]) -> str:
    choices = raw.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, Mapping):
                continue
            message = choice.get("message")
            if isinstance(message, Mapping):
                text = _coerce_text_content(message.get("content"))
                if text:
                    return text
            text = _coerce_text_content(choice.get("text"))
            if text:
                return text
    raise AIClientError("Chat completion response did not include text output")


def _coerce_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, Mapping):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(part.strip() for part in parts if part.strip())
