from __future__ import annotations

from typing import Any

from desktop.ai.config import _endpoint_for_provider
from desktop.ai.models import AIResponse
from desktop.ai.parsers import extract_openai_text
from desktop.ai.providers.base import BaseAIProviderAdapter


class OpenAIProviderAdapter(BaseAIProviderAdapter):
    """Adapter strategy for OpenAI responses API."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image_data_url: str | None = None,
    ) -> AIResponse:
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
        endpoint = _endpoint_for_provider("openai", "/responses")
        raw = self.transport(
            endpoint,
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
            output_text=extract_openai_text(raw),
            raw=raw,
        )
