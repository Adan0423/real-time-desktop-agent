from __future__ import annotations

import pytest

from rtda.ai.client import AIClient, AIClientConfig, AIClientError


def test_openai_client_posts_responses_payload() -> None:
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"output_text": "ok"}

    response = AIClient(
        AIClientConfig(provider="openai", api_key="secret", model="gpt-test"),
        transport=transport,
    ).complete("hello", system="system")

    url, headers, payload, timeout_s = calls[0]
    assert response.output_text == "ok"
    assert url == "https://api.openai.com/v1/responses"
    assert headers["Authorization"] == "Bearer secret"
    assert payload["model"] == "gpt-test"
    assert payload["input"] == "hello"
    assert payload["instructions"] == "system"
    assert payload["store"] is False
    assert timeout_s == 30.0


def test_anthropic_client_posts_messages_payload() -> None:
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"content": [{"type": "text", "text": "done"}]}

    response = AIClient(
        AIClientConfig(provider="anthropic", api_key="secret", model="claude-test"),
        transport=transport,
    ).complete("hello")

    url, headers, payload, _timeout_s = calls[0]
    assert response.output_text == "done"
    assert url == "https://api.anthropic.com/v1/messages"
    assert headers["x-api-key"] == "secret"
    assert headers["anthropic-version"] == "2023-06-01"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]


def test_ai_client_rejects_empty_prompt() -> None:
    client = AIClient(AIClientConfig(provider="openai", api_key="secret"))

    with pytest.raises(AIClientError):
        client.complete("   ")
