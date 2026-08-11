# Progreso

Ultima actualizacion: 2026-08-11

## Resumen

RTDA tiene implementado el nucleo local de captura, metricas, preview, overlay,
percepcion inicial, acciones seguras, agente deterministico y servidor MCP. La
ruta de IA con token existe para texto/contexto, pero aun no envia frames
multimodales a proveedores externos.

## Estado por Modulo

| Modulo / Feature | Estado | Evidencia |
| --- | --- | --- |
| Captura monitor DXGI | ✅ Implementado | `WindowsCaptureEngine`, `--capture-diagnostic` |
| Captura ventana WGC | ✅ Implementado | `--window-title`, backend `wgc` |
| Seleccion de region | ✅ Implementado | `Region`, CLI `--region` |
| Frame buffer | ✅ Implementado | `FrameBuffer`, tests |
| Preview local | ✅ Implementado | `CaptureDashboard` |
| FPS / latencia / drops | ✅ Implementado | `CaptureMetrics`, `docs/performance.md` |
| Overlay verde | ✅ Implementado | `rtda.overlay`, prueba offscreen |
| Diagnostico de captura | ✅ Implementado | `rtda.capture.diagnostics` |
| OpenCV change detection | ✅ Implementado | `OpenCVChangeDetector` |
| Windows UI Automation | ✅ Implementado | `WindowsUIAutomationInspector` |
| OCR adapter | 🚧 Parcial | Adapter y tests fake; runtime Paddle depende de entorno |
| Vision ONNX adapter | 🚧 Parcial | Wrapper ONNX + vision estructurada |
| Acciones seguras | 🚧 Parcial | Motor, risk policy y dry-run; ejecucion real requiere mas hardening |
| Agente observe-plan-act | ✅ Implementado | `AgentExecutor` rule-based |
| MCP server | ✅ Implementado | `health`, `capture_*`, `inspect_uia`, `plan_goal`, `dry_run_action` |
| MCPB manifest Claude | ✅ Implementado | Manifest validado con `mcpb validate` |
| MCPB paquete local | 🚧 Parcial | `.mcpb` generado; falta prueba manual en Claude Desktop |
| Panel IA con token | 🚧 Parcial | OpenAI/Anthropic texto; falta imagen/frame |
| Base de datos | ❌ No implementado | No hay modulo DB |
| CI/CD | ❌ No implementado | No hay workflows `.github` |

## Pruebas

Suite detectada:

```powershell
python -m pytest
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
- overlay geometry.

## Siguiente Hito

El MVP debe cerrar tres puntos:

1. Enviar frame/screenshot al proveedor IA.
2. Probar instalacion manual del `.mcpb` en Claude Desktop.
3. Endurecer permisos y confirmaciones antes de acciones reales.
