# 🔌 Especificación de la API MCP — Real-Time Desktop Agent (RTDA)

> **Versión**: 3.0.1-beta | **Protocolo**: Model Context Protocol (MCP v1.27) | **Transporte**: stdio / SSE

---

## 📑 Visión General del Servidor MCP

El servidor MCP de RTDA (`rtda-mcp`) expone una API unificada para que cualquier cliente o modelo de IA (Claude, Cursor, ChatGPT, etc.) pueda observar la pantalla de Windows en tiempo real, inspeccionar la jerarquía de controles de la UI y ejecutar acciones de mouse/teclado de forma autónoma.

---

## 🧰 Lista Completa de Herramientas Expuestas

### 1. 🔍 `observe_state` (Canal de Datos)
Captura un estado completo de percepción multimodal del escritorio.
* **Parámetros**:
  * `window_title` *(opcional, string)*: Título de la ventana objetivo. Si es `null`, usa la ventana en primer plano.
  * `max_elements` *(opcional, int, default 30)*: Número máximo de elementos UIA a retornar.
* **Retorno**: JSON con la ventana enfocada, aplicación, árbol UIA filtrado y resumen de visión.

### 2. ⚡ `run_task` (Canal de Control Multi-paso)
Ejecuta una tarea autónoma multi-paso utilizando el ciclo completo `OBSERVE → PLAN → ACT → VERIFY → RECOVER`.
* **Parámetros**:
  * `goal` *(string)*: Objetivo en lenguaje natural (ej. `"Hacer clic en Guardar y cerrar el editor"`).
  * `max_steps` *(opcional, int, default 10)*: Límite de seguridad en ciclos de acción.
  * `expected_text` *(opcional, string)*: Texto que valida el éxito de la tarea al aparecer en la UI.
  * `dry_run` *(opcional, bool, default true)*: Si es `true`, simula las acciones sin mover los periféricos físicos. Cambiar a `false` para ejecución real en Windows.
* **Retorno**: Resumen del resultado con flag de éxito, pasos ejecutados, latencia acumulada y telemetría por ciclo.

### 3. 🖱️ `execute_action` (Canal de Acción Individual)
Ejecuta una acción física o simulada de mouse o teclado en el sistema operativo mediante **Win32 `SendInput` (<15ms)**.
* **Parámetros**:
  * `action` *(string)*: Tipo de acción (`"click"`, `"double_click"`, `"right_click"`, `"type"`, `"hotkey"`, `"scroll"`, `"navigate"`).
  * `target` *(opcional, string)*: Nombre o etiqueta del elemento visual objetivo.
  * `value` *(opcional, string)*: Texto a escribir si la acción es `"type"` o URL si es `"navigate"`.
  * `keys` *(opcional, lista de strings)*: Lista de teclas si la acción es `"hotkey"` (ej. `["ctrl", "s"]`).
  * `dry_run` *(opcional, bool, default true)*: Modo simulación. Usar `false` para mover el mouse o teclear físicamente.
* **Retorno**: `ActionResult` en JSON con estado de ejecución y mensaje de confirmación.

### 4. 📑 `desktop_find` (Búsqueda Rápida)
Busca elementos visuales o controles UIA coincidentes en la ventana activa sin solicitar imágenes.
* **Parámetros**:
  * `target` *(string)*: Texto o tipo de control a buscar (coincidencia sin distinción de mayúsculas/minúsculas).
* **Retorno**: Elementos coincidentes con coordenadas de caja delimitadora (`bbox`) y confianza.

### 5. 🪟 `get_focused_window` (Foco Activo)
Retorna información inmediata sobre la ventana que posee el foco actual en Windows.
* **Retorno**: Título de la ventana activa, ejecutable de la aplicación y recuento de elementos UIA.

### 6. 🔎 `inspect_uia` (Inspección UIA Bounded)
Captura una foto acotada del árbol de Windows UI Automation.
* **Parámetros**:
  * `window_title` *(opcional, string)*: Filtro de ventana.
  * `max_depth` *(opcional, int, default 3)*: Profundidad máxima del árbol UIA.
  * `max_elements` *(opcional, int, default 120)*: Límite de elementos.

### 7. 🩺 `health` & `session_status` (Diagnóstico y Telemetría)
* `health`: Retorna el estado del servidor y las fases activas.
* `session_status`: Retorna métricas de tiempo de actividad, FPS de captura y estado de la `DesktopSession` persistente.

### 8. 📷 `capture_monitors` & `capture_diagnostic`
* `capture_monitors`: Lista los monitores físicos detectados en el sistema Windows.
* `capture_diagnostic`: Ejecuta un diagnóstico de rendimiento de captura y calcula latencia y FPS.

---

## 🛡️ Modos de Seguridad (`dry_run`)

Para proteger el entorno del usuario, **todas las herramientas con capacidad de modificación incluyen `dry_run=true` como valor por defecto**.

* **Modo Simulación (`dry_run=true`)**: La herramienta valida la factibilidad de la acción, resuelve coordenadas y verifica la política de seguridad, pero **no mueve el mouse ni presiona teclas físicamente**.
* **Modo Ejecución Real (`dry_run=false`)**: La herramienta envía los comandos de entrada nativos directamente al Kernel de Windows vía **Win32 `SendInput`**.
