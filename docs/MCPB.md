# Claude Desktop MCPB

Ultima actualizacion: 2026-08-11

## Que pide Claude

Cuando Claude Desktop muestra "Arrastra archivos .MCPB o .DXT aqui para
instalar", esta pidiendo un paquete de Desktop Extension.

Segun la documentacion actual de Anthropic:

- `.mcpb` significa MCP Bundle y es el formato recomendado para paquetes nuevos.
- `.dxt` fue el nombre anterior del mismo concepto; sigue existiendo por
  compatibilidad.
- Un `.mcpb` es un ZIP con `manifest.json`, servidor MCP local y dependencias o
  metadata de runtime.

## Estado en RTDA

RTDA ya tiene:

- servidor MCP stdio: `python -m rtda.mcp.server --transport stdio`;
- entrypoint para bundle: `mcpb_server.py`;
- manifiesto base: `packaging/mcpb/manifest.json`;
- `.mcpbignore` para excluir artefactos locales.

El manifest fue validado con el CLI oficial y el paquete local fue generado.
Falta probarlo manualmente en Claude Desktop.

## Comandos

Validar manifest:

```powershell
npx @anthropic-ai/mcpb validate packaging\mcpb\manifest.json
```

Generar paquete:

```powershell
.\scripts\build_mcpb.ps1
```

Resultado local:

```text
dist/real-time-desktop-agent-0.1.0.mcpb
```

El CLI reporta `WARNING: Not signed`, esperado para una build local no
publicada.

Se instala en Claude Desktop de una de estas formas:

1. doble click sobre el `.mcpb`;
2. arrastrar el `.mcpb` a Claude Desktop;
3. Settings -> Extensions -> Advanced settings -> Install Extension.

## Decision Tecnica

RTDA usa un manifiesto `uv` porque el proyecto es Python con `pyproject.toml`.
Esto evita empaquetar manualmente librerias pesadas como `numpy`,
`opencv-python` o `windows-capture`.

## Limitacion

El paquete debe probarse manualmente en Claude Desktop antes de distribuirse. La
firma (`mcpb sign`) queda pendiente para una release publica.

## Fuentes

- [Build a desktop extension with MCPB](https://claude.com/docs/connectors/building/mcpb)
- [Desktop Extensions announcement](https://www.anthropic.com/engineering/desktop-extensions)
- [Claude Desktop local MCP servers](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)
- [MCPB manifest specification](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md)
