from __future__ import annotations

from typing import Any

from desktop.ai.config import _endpoint_for_provider
from desktop.ai.models import AIResponse
from desktop.ai.parsers import extract_anthropic_text, parse_data_url
from desktop.ai.providers.base import BaseAIProviderAdapter


class AnthropicProviderAdapter(BaseAIProviderAdapter):
    """Adapter strategy for Anthropic messages API."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image_data_url: str | None = None,
    ) -> AIResponse:
        model = self.config.resolved_model()
        message_content: str | list[dict[str, Any]] = prompt
        if image_data_url:
            media_type, data = parse_data_url(image_data_url)
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
        endpoint = _endpoint_for_provider("anthropic", "/messages")
        raw = self.transport(
            endpoint,
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
            output_text=extract_anthropic_text(raw),
            raw=raw,
        )
