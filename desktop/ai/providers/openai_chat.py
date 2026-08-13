from __future__ import annotations

from typing import Any

from desktop.ai.config import AIProvider, _chat_endpoint_for_provider, normalize_provider
from desktop.ai.models import AIResponse
from desktop.ai.parsers import extract_chat_completion_text
from desktop.ai.providers.base import BaseAIProviderAdapter
from desktop.ai.transport import DEFAULT_USER_AGENT


def _headers_for_chat_provider(provider: AIProvider, api_key: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/Adan0423/real-time-desktop-agent"
        headers["X-OpenRouter-Title"] = "Real-Time Desktop Agent"
    if provider == "nvidia":
        headers["Accept"] = "application/json"
    return headers


class OpenAIChatProviderAdapter(BaseAIProviderAdapter):
    """Adapter strategy for OpenAI-compatible chat completion APIs (Groq, OpenRouter, TokenRouter, NVIDIA, etc.)."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image_data_url: str | None = None,
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
        endpoint = _chat_endpoint_for_provider(provider)
        headers = _headers_for_chat_provider(provider, self.config.resolved_api_key())
        raw = self.transport(
            endpoint,
            headers,
            payload,
            self.config.timeout_s,
        )
        return AIResponse(
            provider=provider,
            model=model,
            output_text=extract_chat_completion_text(raw),
            raw=raw,
        )
