# Real-Time Desktop Agent Plugin

Este paquete expone `real-time-desktop-agent` como plugin local para ChatGPT
Desktop y Codex.

Contenido:

- `.codex-plugin/plugin.json`: manifiesto requerido por OpenAI Plugins.
- `.mcp.json`: servidor MCP local que ejecuta `python -m rtda.mcp.server`.

Requisito antes de instalar:

```powershell
python -m pip install -e ".[capture,gui,dev]"
```

Este paquete no es `.mcpb`; `.mcpb` es para Claude Desktop. ChatGPT/Codex usa
Plugins con `.codex-plugin/plugin.json` y MCP.
