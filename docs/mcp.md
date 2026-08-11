# MCP

## Fase 8

El servidor MCP vive en `src/rtda/mcp/server.py`.

```powershell
python -m rtda.mcp.server --transport stdio
```

Herramientas:

- `health`
- `capture_monitors`
- `capture_diagnostic`
- `inspect_uia`
- `plan_goal`
- `classify_action`
- `dry_run_action`

No expone ejecucion real de acciones. `dry_run_action` usa el mismo motor de seguridad y resolucion, pero con executor seco.

## Uso como complemento

Este modo es para hosts compatibles con MCP. RTDA corre como proceso local y el
host externo llama tools por stdio, HTTP streamable o SSE segun soporte del host.

```powershell
python -m rtda.mcp.server --transport stdio
```

`capture_diagnostic` permite que un host externo valide captura real sin abrir
la app completa. Devuelve checks, monitores, frame mas reciente y metricas.
