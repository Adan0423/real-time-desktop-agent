from __future__ import annotations

import pytest

from rtda.ai.client import AIClient, AIClientConfig, AIClientError, default_model


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


@pytest.mark.parametrize(
    ("provider", "endpoint", "model"),
    (
        ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free"),
        ("groq", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
        ("tokenrouter", "https://api.tokenrouter.io/v1/chat/completions", "auto:cost"),
        ("nvidia", "https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.3-70b-instruct"),
    ),
)
def test_openai_compatible_chat_provider_posts_payload(provider: str, endpoint: str, model: str) -> None:
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"choices": [{"message": {"role": "assistant", "content": "chat ok"}}]}

    response = AIClient(
        AIClientConfig(provider=provider, api_key="secret", max_output_tokens=123),
        transport=transport,
    ).complete("hello", system="system")

    url, headers, payload, timeout_s = calls[0]
    assert response.provider == provider
    assert response.model == model
    assert response.output_text == "chat ok"
    assert url == endpoint
    assert headers["Authorization"] == "Bearer secret"
    assert headers["Content-Type"] == "application/json"
    assert payload["model"] == model
    assert payload["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "hello"},
    ]
    assert payload["max_tokens"] == 123
    assert payload["stream"] is False
    assert timeout_s == 30.0


def test_openrouter_and_nvidia_send_provider_specific_headers() -> None:
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append(headers)
        return {"choices": [{"message": {"content": "ok"}}]}

    AIClient(AIClientConfig(provider="openrouter", api_key="secret"), transport=transport).complete("hello")
    AIClient(AIClientConfig(provider="nvidia", api_key="secret"), transport=transport).complete("hello")

    assert calls[0]["HTTP-Referer"].startswith("https://github.com/")
    assert calls[0]["X-OpenRouter-Title"] == "Real-Time Desktop Agent"
    assert calls[1]["Accept"] == "application/json"


def test_ai_config_from_env_supports_new_providers(monkeypatch) -> None:
    monkeypatch.setenv("RTDA_AI_PROVIDER", "qroq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-secret")

    config = AIClientConfig.from_env()

    assert config.provider == "groq"
    assert config.api_key == "gsk-secret"
    assert config.model == default_model("groq")


def test_ai_client_rejects_empty_prompt() -> None:
    client = AIClient(AIClientConfig(provider="openai", api_key="secret"))

    with pytest.raises(AIClientError):
        client.complete("   ")
