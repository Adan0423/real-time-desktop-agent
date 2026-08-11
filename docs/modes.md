# Modos de uso

RTDA tiene dos superficies de uso y una frontera comun.

```text
RTDA Complement
|-- consumido por Desktop Control Surface
`-- consumido por hosts IA mediante MCP/MCPB
```

## App propia

La app local sirve para pruebas visuales controladas:

```powershell
python -m rtda.app.main
```

Incluye:

- captura de monitor, region o ventana;
- preview en tiempo real;
- FPS, resolucion, latencia, frames perdidos y errores;
- borde verde sobre el area capturada;
- control flotante topmost para ver si RTDA esta activo;
- panel IA con proveedor, modelo, token y prompt.

El token de IA se mantiene en memoria. Tambien puede resolverse desde variables
de entorno si existen (`OPENAI_API_KEY` o `ANTHROPIC_API_KEY`), pero RTDA no
escribe secretos en el repositorio.

Opciones utiles:

```powershell
python -m rtda.app.main --hide-overlay
python -m rtda.app.main --hide-floating
python -m rtda.app.main --enable-perception-tools
```

## Complemento para IA externa

El servidor MCP es la superficie para clientes externos compatibles con tools:

```powershell
python -m rtda.mcp.server --transport stdio
```

Esta ruta permite que un host como ChatGPT, Claude, Codex u otro agente
compatible consuma herramientas de RTDA sin depender de la UI local. El
complemento expone captura diagnostica, inspeccion UIA, planificacion simple,
clasificacion de riesgo y acciones en modo seco.

Para Claude Desktop, RTDA tambien puede empaquetarse como `.mcpb`:

```powershell
.\scripts\build_mcpb.ps1
```

Luego se instala arrastrando el archivo `.mcpb` generado a Claude Desktop.
`.dxt` es el nombre heredado del formato; el paquete nuevo debe publicarse como
`.mcpb`.

Por seguridad, el MCP no ejecuta acciones reales. Mantiene `dry_run_action`
como frontera inicial para pruebas.
