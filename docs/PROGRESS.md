# Progreso

Ultima actualizacion: 2026-08-11

## Resumen

RTDA tiene implementado el nucleo local de captura, metricas, preview, overlay,
percepcion inicial, acciones seguras, agente deterministico y servidor MCP. La
arquitectura ya separa el complemento funcional (`src/rtda`) de la app de
escritorio (`desktop/`). `rtda.app` queda como launcher y `rtda.extension`
como ruta compatible para imports antiguos.

La ruta de IA con token existe para texto/contexto, pero aun no envia frames
multimodales a proveedores externos.

## Estado por Modulo

| Modulo / Feature | Estado | Evidencia |
| --- | --- | --- |
| Captura monitor DXGI | Implementado | `WindowsCaptureEngine`, `--capture-diagnostic` |
| Captura ventana WGC | Implementado | `--window-title`, backend `wgc` |
| Seleccion de region | Implementado | `Region`, CLI `--region`, inputs en dashboard |
| Frame buffer | Implementado | `FrameBuffer`, tests |
| Runtime de complemento | Implementado | `RTDAComplementRuntime`, `tests/test_extension_runtime.py` |
| Desktop Control Surface | Implementado | `CaptureDashboard` compacto, `desktop/ui/*`, instancia offscreen verificada |
| Control flotante | Implementado | `RTDAFloatingControl` compacto, `tests/test_desktop_floating.py` |
| Preview local | Implementado | `PreviewPanel` en `desktop/ui/preview.py` |
| FPS / latencia / drops | Implementado | `CaptureMetrics`, `docs/performance.md` |
| Overlay verde | Implementado | `rtda.overlay`, prueba offscreen |
| Diagnostico de captura | Implementado | `rtda.capture.diagnostics` |
| OpenCV change detection | Implementado | `OpenCVChangeDetector`, `RTDAComplementRuntime.detect_changes()` |
| Windows UI Automation | Implementado | `WindowsUIAutomationInspector` |
| Mouse/teclado runtime | Implementado | `RTDAComplementRuntime.click()`, `hotkey()`, `press()` |
| OCR adapter | Parcial | Adapter y tests fake; runtime Paddle depende de entorno |
| Vision ONNX adapter | Parcial | Wrapper ONNX + vision estructurada |
| Acciones seguras | Parcial | Motor, risk policy y dry-run; ejecucion real requiere mas hardening |
| Agente observe-plan-act | Implementado | `AgentExecutor` rule-based |
| MCP server | Implementado | `health`, `capture_*`, `inspect_uia`, `plan_goal`, `dry_run_action` |
| MCPB manifest Claude | Implementado | Manifest validado con `mcpb validate` |
| MCPB paquete local | Parcial | `.mcpb` generado; falta prueba manual en Claude Desktop |
| Plugin local ChatGPT/Codex | Implementado | `.codex-plugin/plugin.json`, `.mcp.json`, marketplace repo |
| Panel IA con token | Parcial | OpenAI/Anthropic texto; falta imagen/frame |
| Base de datos | No implementado | No hay modulo DB |
| CI/CD | No implementado | No hay workflows `.github` |

## Pruebas

Suite actual:

```powershell
python -m pytest
```

Resultado local del 2026-08-11:

```text
47 passed
```

Verificaciones adicionales:

```powershell
python -m compileall src\rtda tests
```

```text
dashboard instantiated
```

Cobertura funcional actual por archivos:

- captura y lifecycle Windows;
- frame buffer y regiones;
- metricas;
- OpenCV change detection;
- UIA;
- OCR adapter fake;
- vision model;
- acciones y safety;
- agente;
- MCP server;
- AI client;
- overlay geometry;
- runtime de complemento;
- control flotante Qt.

## Siguiente Hito

El MVP debe cerrar cuatro puntos:

1. Enviar frame/screenshot al proveedor IA.
2. Probar instalacion manual del `.mcpb` en Claude Desktop.
3. Convertir el runtime in-process en opcion de servicio local persistente.
4. Endurecer permisos y confirmaciones antes de acciones reales.
