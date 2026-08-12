# IA con token

## Objetivo

La app propia de RTDA incluye un panel IA para pruebas controladas. Este panel
usa un cliente interno pequeno (`rtda.ai.AIClient`) con varios proveedores:

| Proveedor | API | Endpoint | Token |
| --- | --- | --- | --- |
| OpenAI | Responses API | `POST /v1/responses` | `OPENAI_API_KEY` o campo UI |
| Anthropic | Messages API | `POST /v1/messages` | `ANTHROPIC_API_KEY` o campo UI |
| OpenRouter | Chat Completions compatible | `POST /api/v1/chat/completions` | `OPENROUTER_API_KEY` o campo UI |
| Groq | Chat Completions compatible | `POST /openai/v1/chat/completions` | `GROQ_API_KEY` o campo UI |
| TokenRouter | Chat Completions compatible | `POST /v1/chat/completions` | `TOKENROUTER_API_KEY` o campo UI |
| NVIDIA NIM | Chat Completions compatible | `POST /v1/chat/completions` | `NVIDIA_API_KEY` o campo UI |

Modelos por defecto:

- OpenAI: `gpt-5.6-terra`
- Anthropic: `claude-sonnet-5`
- OpenRouter: `openrouter/free`
- Groq: `llama-3.3-70b-versatile`
- TokenRouter: `auto:cost`
- NVIDIA NIM: `meta/llama-3.3-70b-instruct`

## Decisiones

- No se agregan dependencias nuevas: el cliente usa `urllib` y JSON.
- El token se usa solo en memoria o desde entorno si ya existe.
- OpenAI se llama con `store=false` para evitar almacenamiento intencional de
  estado de respuesta desde RTDA.
- Anthropic se llama con el header estable `anthropic-version: 2023-06-01`.
- OpenRouter, Groq, TokenRouter y NVIDIA usan una ruta comun compatible con
  OpenAI Chat Completions.
- `RTDA_AI_PROVIDER=qroq` se normaliza a `groq` para tolerar ese typo.
- El modelo queda editable en la UI porque los planes gratis, disponibilidad y
  rate limits cambian por proveedor.
- Las pruebas usan transporte fake; no hacen llamadas reales ni requieren token.

## Fuentes consultadas

- [OpenAI API quickstart](https://platform.openai.com/docs/quickstart/make-your-first-api-request)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)
- [OpenAI Models](https://developers.openai.com/api/docs/models)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart)
- [OpenRouter Free Models Router](https://openrouter.ai/docs/guides/routing/routers/free-router)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [TokenRouter OpenAI Compatibility](https://docs.tokenrouter.io/getting-started/openai-compatibility/)
- [NVIDIA NIM LLM APIs](https://docs.api.nvidia.com/nim/reference/llm-apis)

## Estado

Implementado:

- `AIClientConfig`
- `AIClient`
- `AIResponse`
- adaptador OpenAI
- adaptador Anthropic
- adaptador compatible Chat Completions para OpenRouter/Groq/TokenRouter/NVIDIA
- panel IA en dashboard
- pruebas unitarias sin red

No implementado todavia:

- envio de screenshot o frame codificado al modelo;
- streaming;
- tool calling directo desde el proveedor IA.
