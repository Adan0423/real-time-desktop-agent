from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from desktop.ai.config import AIProvider


@dataclass(frozen=True, slots=True)
class AIResponse:
    provider: AIProvider
    model: str
    output_text: str
    raw: Mapping[str, Any]
