# IA con token

## Objetivo

La app propia de RTDA incluye un panel IA para pruebas controladas. Este panel
usa un cliente interno pequeno (`desktop.ai.AIClient`) con varios proveedores:

| Proveedor | API | Endpoint | Token |
| --- | --- | --- | --- |
| OpenAI | Responses API | `POST /v1/responses` | `OPENAI_API_KEY` o campo UI |
| Anthropic | Messages API | `POST /v1/messages` | `ANTHROPIC_API_KEY` o campo UI |
| OpenRouter | Chat Completions compatible | `POST /api/v1/chat/completions` | `OPENROUTER_API_KEY` o campo UI |
| Groq | Chat Completions compatible | `POST /openai/v1/chat/completions` | `GROQ_API_KEY` o campo UI |
| TokenRouter | Chat Completions compatible | `POST https://api.tokenrouter.com/v1/chat/completions` | `TOKENROUTER_API_KEY` o campo UI |
| NVIDIA NIM | Chat Completions compatible | `POST /v1/chat/completions` | `NVIDIA_API_KEY` o campo UI |

Modelos por defecto:

- OpenAI: `gpt-5.6-terra`
- Anthropic: `claude-sonnet-5`
- OpenRouter: `openrouter/free`
- Groq: `llama-3.3-70b-versatile`
- TokenRouter: `moonshotai/kimi-k3-free`
- NVIDIA NIM: `meta/llama-3.3-70b-instruct`

## Decisiones

- No se agregan dependencias nuevas: el cliente usa `urllib` y JSON.
- El token se usa solo en memoria o desde entorno si ya existe.
- RTDA no carga `.env` automaticamente. Si usas variables de entorno, debes
  definirlas en la sesion antes de abrir la app.
- La respuesta se muestra en la caja de salida del panel IA, debajo del boton
  `Consultar IA`.
- Cada consulta usa una observacion visual viva de RTDA, si la captura esta
  activa. Es una muestra transitoria del estado actual del escritorio para esa
  solicitud, no un historial, una grabacion ni una sesion de video.
- La codificacion necesaria para enviar la observacion al proveedor ocurre solo
  en RAM y se libera al finalizar la solicitud. RTDA no escribe screenshots ni
  frames a disco.
- OpenAI se llama con `store=false` para evitar almacenamiento intencional de
  estado de respuesta desde RTDA.
- Anthropic se llama con el header estable `anthropic-version: 2023-06-01`.
- OpenRouter, Groq, TokenRouter y NVIDIA usan una ruta comun compatible con
  OpenAI Chat Completions.
- `RTDA_AI_PROVIDER=qroq` se normaliza a `groq` para tolerar ese typo.
- El preset TokenRouter usa `moonshotai/kimi-k3-free`; al ser free, su
  capacidad, estabilidad y concurrencia dependen del proveedor. Free no
  significa sin token: TokenRouter igual requiere `TOKENROUTER_API_KEY`.
  Si el modelo seleccionado es solo texto, el proveedor puede rechazar o
  ignorar la observacion visual. Para preguntas como "que puedes ver", elige
  un modelo multimodal compatible con imagen.
- `TOKENROUTER_BASE_URL` permite cambiar la URL base. Acepta valores como
  `https://api.tokenrouter.com/v1` o la ruta completa
  `https://api.tokenrouter.com/v1/chat/completions`.
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

- streaming;
- ciclo de herramientas directo entre un proveedor IA y las acciones RTDA.

## Alcance de tiempo real

RTDA es el runtime local que permite a una IA observar el escritorio, consultar
UI Automation y ejecutar acciones permitidas de mouse o teclado. La app de
escritorio es una superficie de prueba de ese runtime.

El panel IA actual realiza una consulta puntual con el estado vivo disponible.
No abre un canal de video continuo con los proveedores, porque los endpoints
Chat Completions de los proveedores configurados son solicitudes HTTP discretas.
Para un agente autonomo, el siguiente paso es un ciclo controlado:

`observar estado vivo -> planificar -> solicitar/validar accion RTDA -> verificar nuevo estado`

Las acciones no se entregan automaticamente al proveedor desde este panel. Se
mantienen detras de `ActionGuard`, dry-run y confirmaciones para evitar que una
respuesta remota controle el escritorio sin limites.
