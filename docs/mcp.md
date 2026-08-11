# MCP

## Fase 8

El servidor MCP vive en `src/rtda/mcp/server.py`.

```powershell
python -m rtda.mcp.server --transport stdio
```

Herramientas:

- `health`
- `inspect_uia`
- `plan_goal`
- `classify_action`
- `dry_run_action`

No expone ejecucion real de acciones. `dry_run_action` usa el mismo motor de seguridad y resolucion, pero con executor seco.
