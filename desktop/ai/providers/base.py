from __future__ import annotations

from abc import ABC, abstractmethod

from desktop.ai.config import AIClientConfig
from desktop.ai.models import AIResponse
from desktop.ai.transport import Transport


class BaseAIProviderAdapter(ABC):
    """Abstract base strategy for AI provider integration adapters."""

    def __init__(self, config: AIClientConfig, transport: Transport) -> None:
        self.config = config
        self.transport = transport

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image_data_url: str | None = None,
    ) -> AIResponse:
        """Execute a completion request against the target AI provider."""
