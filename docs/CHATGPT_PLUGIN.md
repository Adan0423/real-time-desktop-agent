# ChatGPT / Codex Plugin

Ultima actualizacion: 2026-08-11

## Decision

ChatGPT no instala complementos locales como archivo `.mcpb`. Segun la
documentacion oficial de OpenAI, ChatGPT y Codex usan **Plugins/Apps** con un
manifiesto `.codex-plugin/plugin.json`. Un plugin puede incluir skills, un MCP
server o ambos.

Para RTDA:

- Claude Desktop: paquete `.mcpb`.
- ChatGPT/Codex local: plugin con `.codex-plugin/plugin.json` y `.mcp.json`.
- ChatGPT web/produccion: MCP server remoto por HTTPS, normalmente en `/mcp`.

## Estructura creada

```text
plugins/real-time-desktop-agent/
|-- .codex-plugin/
|   `-- plugin.json
|-- .mcp.json
`-- README.md

.agents/plugins/
`-- marketplace.json
```

El plugin local usa el servidor MCP existente:

```powershell
python -m rtda.mcp.server --transport stdio
```

## Instalacion local en ChatGPT Desktop / Codex

1. Instalar el proyecto en editable desde la raiz:

```powershell
python -m pip install -e ".[capture,gui,dev]"
```

2. Reiniciar ChatGPT Desktop.

3. Abrir el directorio de Plugins.

4. Seleccionar el marketplace local `RTDA Local Plugins`.

5. Instalar `Real-Time Desktop Agent`.

La configuracion del marketplace vive en:

```text
.agents/plugins/marketplace.json
```

## Prueba con ChatGPT Developer Mode

Para probar como MCP server remoto:

1. Levantar el servidor MCP con transporte HTTP:

```powershell
python -m rtda.mcp.server --transport streamable-http
```

2. Exponer el endpoint con HTTPS o Secure MCP Tunnel.

3. En ChatGPT, habilitar Developer Mode.

4. Crear una conexion MCP usando la URL publica con ruta `/mcp`.

5. Verificar herramientas, metadata, confirmaciones y respuestas.

## Publicacion

Para publicar publicamente en ChatGPT/Codex, OpenAI requiere envio por el portal
de plugin submission. El plugin puede ser:

- skills-only;
- MCP-only;
- MCP + skills.

Para un plugin con MCP se debe preparar:

- URL publica del MCP server;
- metadata correcta de tools;
- anotaciones de seguridad (`readOnlyHint`, `openWorldHint`, `destructiveHint`);
- identidad de desarrollador verificada;
- politicas, privacidad, prompts de prueba y casos positivos/negativos.

## Fuentes oficiales

- [Package your plugin](https://developers.openai.com/plugins/build/plugins)
- [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Submit plugins](https://developers.openai.com/plugins/deploy/submission)
