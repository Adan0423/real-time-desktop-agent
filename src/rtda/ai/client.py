from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

AIProvider = Literal["openai", "anthropic"]
Transport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]


class AIClientError(RuntimeError):
    """Raised when an AI provider request cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class AIClientConfig:
    provider: AIProvider = "openai"
    api_key: str | None = None
    model: str | None = None
    timeout_s: float = 30.0
    max_output_tokens: int = 800

    @classmethod
    def from_env(cls, provider: AIProvider | None = None) -> "AIClientConfig":
        selected_provider = provider or os.getenv("RTDA_AI_PROVIDER", "openai").strip().lower()
        if selected_provider not in ("openai", "anthropic"):
            raise ValueError("RTDA_AI_PROVIDER must be 'openai' or 'anthropic'")
        api_key = os.getenv("OPENAI_API_KEY") if selected_provider == "openai" else os.getenv("ANTHROPIC_API_KEY")
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
        env_name = "OPENAI_API_KEY" if self.provider == "openai" else "ANTHROPIC_API_KEY"
        env_value = os.getenv(env_name)
        if env_value:
            return env_value
        raise AIClientError(f"missing API token for provider '{self.provider}'")


@dataclass(frozen=True, slots=True)
class AIResponse:
    provider: AIProvider
    model: str
    output_text: str
    raw: Mapping[str, Any]


def default_model(provider: AIProvider) -> str:
    if provider == "openai":
        return "gpt-5.6-terra"
    if provider == "anthropic":
        return "claude-sonnet-5"
    raise ValueError("provider must be 'openai' or 'anthropic'")


class AIClient:
    def __init__(self, config: AIClientConfig, *, transport: Transport | None = None) -> None:
        self.config = config
        self._transport = transport or _post_json

    def complete(self, prompt: str, *, system: str | None = None) -> AIResponse:
        prompt = prompt.strip()
        if not prompt:
            raise AIClientError("prompt is empty")
        if self.config.provider == "openai":
            return self._complete_openai(prompt, system=system)
        if self.config.provider == "anthropic":
            return self._complete_anthropic(prompt, system=system)
        raise AIClientError(f"unsupported provider: {self.config.provider}")

    def _complete_openai(self, prompt: str, *, system: str | None) -> AIResponse:
        model = self.config.resolved_model()
        payload: dict[str, Any] = {
            "model": model,
            "input": prompt,
            "store": False,
            "max_output_tokens": self.config.max_output_tokens,
        }
        if system:
            payload["instructions"] = system
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

    def _complete_anthropic(self, prompt: str, *, system: str | None) -> AIResponse:
        model = self.config.resolved_model()
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.config.max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
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
    except TimeoutError as exc:
        raise AIClientError("AI provider request timed out") from exc
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
