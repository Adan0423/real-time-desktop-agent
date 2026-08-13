# 📦 Plan de Compatibilidad, Empaquetado y Entorno (RTDA)

> **Documento Técnico de Portabilidad, Empaquetado MCP y Entornos de Ejecución**

---

## 🎯 1. Diagnóstico y Prioridades

El conector expone 13 herramientas MCP. Sin embargo, el subsistema de observación real depende directamente de las APIs nativas de Windows (`COM`, `UI Automation`, `DXGI/WGC` y `Win32 SendInput`).

Al ejecutar RTDA en entornos no Windows (Linux/macOS), la función `observe_state` debe fallar de forma controlada indicando la incompatibilidad de plataforma, manteniendo funcionales las herramientas agnósticas al SO.

---

## 📋 2. Matriz de Acciones de Mejora

| Prioridad | Área / Mejora | Motivo y Acción Concreta |
|---|---|---|
| 🔴 **Alta** | **Ejecución en Windows 10/11** | UIA, COM, DXGI/WGC y Win32 SendInput son los cimientos de la observación/control real. Instalar y arrancar en un entorno Windows nativo. |
| 🔴 **Alta** | **Fijar MCP `< 2.0`** | El código usa `mcp.server.fastmcp`. Fijar `mcp>=1.27,<2` de forma explícita en `pyproject.toml`, en el wheel publicado y en el lockfile. |
| 🔴 **Alta** | **Corregir Metadatos del Wheel** | El `pyproject.toml` exige `MCP <2`, pero el wheel publicado permitió versiones mayores. Reconstruir y republicar el paquete. |
| 🔴 **Alta** | **Entorno Virtual Dedicado (`.venv`)** | Configurar el conector especificando la ruta ejecutable del Python en `.venv` de RTDA, evitando el uso de Python global. |
| 🟡 **Media** | **Detección Automática de SO** | Antes de instanciar `DesktopSession`, verificar la plataforma (`sys.platform != "win32"`) y emitir un diagnóstico explícito. |
| 🟡 **Media** | **Separar Herramientas Nativas vs Portables** | `health`, `plan_goal`, `classify_action` y el modo `dry_run` son portables. Registrar herramientas de captura/UIA solo cuando el backend de Windows esté disponible. |
| 🟡 **Media** | **Unificar Versión y Documentación** | Sincronizar las etiquetas de versión entre la guía (0.1.0) y la versión de paquete/release (3.0.0b1). |
| 🟡 **Media** | **Prueba de Arranque Automatizada** | Agregar un test de integración que verifique: importación, `health`, listado de herramientas MCP y detección del backend Windows. |

---

## 🧪 3. Guía de Verificación en Windows

Para realizar una verificación completa en Windows (Python 3.12–3.14):

```bash
# 1. Iniciar el servidor MCP vía stdio
python -m rtda.mcp.server --transport stdio

# 2. Probar herramientas de diagnóstico básicas
health
session_status

# 3. Probar la observación real con dry_run activado
observe_state dry_run: true
```
