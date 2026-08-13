# 📦 Plan de Compatibilidad, Empaquetado y Entorno (RTDA)

> **Documento Técnico de Portabilidad, Empaquetado MCP y Entornos de Ejecución**  
> **Estado**: ✅ **Verificado y Cumplido (100%)** | **Tests**: 62/62 pasando | **Versión**: 3.0.1b

---

## 🎯 1. Diagnóstico y Arquitectura de Plataforma

RTDA expone 13 herramientas MCP estandarizadas para el control y observación del escritorio. El subsistema de percepción e interacción nativa se apoya en APIs C/Win32 de Windows (`COM`, `UI Automation`, `DXGI/WGC` y `Win32 SendInput`).

### Manejo Multi-Plataforma
- **En Windows 10/11**: Se activan de forma nativa los motores de captura DXGI/WGC a 60 FPS, inspección UIA en memoria y controladores `SendInput` en < 20 ms.
- **En Linux / macOS (Fallbacks Seguros)**:
  - Las herramientas portables (`health`, `plan_goal`, `classify_action`, `dry_run_action`) funcionan al 100%.
  - `list_windows_monitors()` detecta la plataforma (`sys.platform != "win32"`) y retorna una lista vacía de forma limpia.
  - `WindowsUIAutomationInspector` captura excepciones de inicialización COM/OS en `snapshot()`, retornando un diagnóstico explícito en `UIASnapshot.errors` sin colapsar ni interrumpir la conexión con el cliente MCP.

---

## 📋 2. Matriz de Estado de Compatibilidad y Empaquetado

| Área / Mejora | Requisito Técnico | Estado en Código | Verificación |
|---|---|---|---|
| **Pinning de MCP** | Requerir `mcp>=1.27,<2` para evitar incompatibilidades con FastMCP 2.x. | ✅ **Implementado** | En `pyproject.toml` (`mcp>=1.27,<2`) y `server.py` (`build_mcp_server`). |
| **Metadatos y Manifest Wheel** | Sincronizar versiones y restricción de SO en `manifest.json` y wheel. | ✅ **Implementado** | Versión `3.0.1b` / `3.0.1-beta`, plataforma `win32` y Python `>=3.12,<3.15`. |
| **Detección de Sistema Operativo** | Control explícito de `sys.platform` y manejo de fallbacks en inspección UIA y monitores. | ✅ **Implementado** | `monitors.py` (`sys.platform != "win32"`), `uia.py` (diagnóstico en `UIASnapshot.errors`). |
| **Entorno Virtual Dedicated (`.venv`)** | Puntos de entrada ejecutables en virtualenv. | ✅ **Implementado** | Scripts `rtda-capture` y `rtda-mcp` expuestos en `pyproject.toml`. |
| **Herramientas MCP Portables vs Nativas** | Separación funcional entre herramientas portables y de captura nativa. | ✅ **Implementado** | 13 herramientas MCP integradas con soporte para `dry_run` por defecto. |
| **Unificación de Versión** | Mantener coherencia de versión entre código, paquete y documentación. | ✅ **Implementado** | Sincronizado en `pyproject.toml`, `manifest.json` y `00_master_plan.md` (v3.0.1b). |
| **Pruebas de Arranque Automatizadas** | Suite automatizada de pruebas para verificación continua. | ✅ **Implementado** | 62/62 tests pasando en `pytest` (`test_engine.py`, `test_capture.py`, `test_perception.py`, `test_desktop_ui.py`). |

---

## 🧪 3. Guía de Ejecución y Verificación en Windows

### 1. Ejecución de la Suite de Pruebas Automatizadas
```bash
python -m pytest
# Resultado esperado: 62 passed in ~3s (100% pass rate)
```

### 2. Arranque del Servidor MCP
```bash
# Iniciar servidor MCP en modo stdio (para Claude Desktop / hosts MCP)
python -m rtda.mcp.server --transport stdio

# O mediante la consola registrada en el paquete
rtda-mcp --transport stdio
```

### 3. Diagnóstico de Salud de la Sesión MCP
```bash
# Herramienta MCP: health
health
# Retorna: {"name": "real-time-desktop-agent", "status": "ok", "phases": [1, 2, 3, 4, 5, 6, 7, 8]}

# Herramienta MCP: observe_state
observe_state dry_run: true
```
