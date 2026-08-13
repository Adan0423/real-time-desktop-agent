from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from desktop.ai.exceptions import AIClientError


def parse_data_url(data_url: str) -> tuple[str, str]:
    prefix, separator, data = data_url.partition(",")
    if not separator or not prefix.startswith("data:") or ";base64" not in prefix:
        raise AIClientError("image payload must be a base64 data URL")
    media_type = prefix.removeprefix("data:").split(";", 1)[0]
    return media_type, data


def extract_openai_text(raw: Mapping[str, Any]) -> str:
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


def extract_anthropic_text(raw: Mapping[str, Any]) -> str:
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


def extract_chat_completion_text(raw: Mapping[str, Any]) -> str:
    choices = raw.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, Mapping):
                continue
            message = choice.get("message")
            if isinstance(message, Mapping):
                text = coerce_text_content(message.get("content"))
                if text:
                    return text
            text = coerce_text_content(choice.get("text"))
            if text:
                return text
    raise AIClientError("Chat completion response did not include text output")


def coerce_text_content(content: Any) -> str:
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
