# Skills

Ultima actualizacion: 2026-08-11

## Inventario de Capacidades

| Skill | Estado | Entrada principal | Ejemplo |
| --- | --- | --- | --- |
| Listar monitores | ✅ | CLI/MCP | `python -m rtda.app.main --list-monitors` |
| Capturar monitor | ✅ | backend + monitor | `--backend dxgi --monitor-index 0` |
| Capturar region | ✅ | coordenadas | `--region 0 0 320 240` |
| Capturar ventana | ✅ | titulo ventana | `--window-title ChatGPT` |
| Diagnostico de captura | ✅ | duracion/backend | `--capture-diagnostic --duration 4` |
| Preview local | ✅ | dashboard | `python -m rtda.app.main` |
| Overlay verde | ✅ | config captura | activo por defecto |
| Deteccion de cambios | ✅ | frame pair | `--detect-changes` |
| Snapshot UIA | ✅ | titulo opcional | `--inspect-uia --uia-max-depth 3` |
| OCR | 🚧 | frame/region | `PaddleOCREngine.analyze(frame)` |
| Vision estructurada | 🚧 | frame + elementos | `StructuredVisionModel` |
| Clasificar accion | ✅ | accion/target | MCP `classify_action` |
| Accion dry-run | ✅ | accion/target/value | MCP `dry_run_action` |
| Planificar meta | ✅ | goal texto | MCP `plan_goal` |
| IA con token | 🚧 | prompt/proveedor | `AIClient.complete(...)` |
| MCPB Claude | 🚧 | manifest | `packaging/mcpb/manifest.json` |

## Ejemplos CLI

```powershell
python -m rtda.app.main --list-monitors
python -m rtda.app.main --capture-diagnostic --duration 4 --backend dxgi
python -m rtda.app.main --headless --duration 5 --detect-changes
python -m rtda.app.main --headless --duration 0 --inspect-uia --uia-max-depth 3
python -m rtda.mcp.server --transport stdio
```

## Ejemplos Python

```python
from rtda.ai import AIClient, AIClientConfig

client = AIClient(AIClientConfig(provider="openai", api_key="..."))
response = client.complete("Resume el estado de captura.")
print(response.output_text)
```

```python
from rtda.capture.interface import CaptureConfig
from rtda.capture.windows_capture import WindowsCaptureEngine

capture = WindowsCaptureEngine(CaptureConfig(backend="dxgi", target_fps=30))
capture.start()
frame = capture.latest_frame()
capture.stop()
```

## Tools MCP

| Tool | Uso recomendado |
| --- | --- |
| `health` | Confirmar que RTDA responde |
| `capture_monitors` | Ver que pantallas puede observar RTDA |
| `capture_diagnostic` | Validar captura antes de depender de frames |
| `inspect_uia` | Leer estructura UI cuando OCR no basta |
| `plan_goal` | Probar planner deterministico |
| `classify_action` | Evaluar seguridad antes de ejecutar |
| `dry_run_action` | Simular accion sin tocar el escritorio |

## Criterio de Uso

Usa captura y diagnostico antes de cualquier pipeline de percepcion. Usa
`classify_action` y `dry_run_action` antes de permitir automatizacion real.
