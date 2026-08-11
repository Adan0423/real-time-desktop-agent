# IA con token

## Objetivo

La app propia de RTDA incluye un panel IA para pruebas controladas. Este panel
usa un cliente interno pequeno (`rtda.ai.AIClient`) con dos proveedores:

| Proveedor | API | Endpoint | Token |
| --- | --- | --- | --- |
| OpenAI | Responses API | `POST /v1/responses` | `OPENAI_API_KEY` o campo UI |
| Anthropic | Messages API | `POST /v1/messages` | `ANTHROPIC_API_KEY` o campo UI |

Modelos por defecto:

- OpenAI: `gpt-5.6-terra`
- Anthropic: `claude-sonnet-5`

## Decisiones

- No se agregan dependencias nuevas: el cliente usa `urllib` y JSON.
- El token se usa solo en memoria o desde entorno si ya existe.
- OpenAI se llama con `store=false` para evitar almacenamiento intencional de
  estado de respuesta desde RTDA.
- Anthropic se llama con el header estable `anthropic-version: 2023-06-01`.
- Las pruebas usan transporte fake; no hacen llamadas reales ni requieren token.

## Fuentes consultadas

- [OpenAI API quickstart](https://platform.openai.com/docs/quickstart/make-your-first-api-request)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)
- [OpenAI Models](https://developers.openai.com/api/docs/models)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview)

## Estado

Implementado:

- `AIClientConfig`
- `AIClient`
- `AIResponse`
- adaptador OpenAI
- adaptador Anthropic
- panel IA en dashboard
- pruebas unitarias sin red

No implementado todavia:

- envio de screenshot o frame codificado al modelo;
- streaming;
- tool calling directo desde el proveedor IA.
