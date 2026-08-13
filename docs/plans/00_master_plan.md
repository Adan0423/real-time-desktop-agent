# 🌟 MASTER PLAN v3.0 — REAL-TIME DESKTOP AGENT

> **Documento Maestro de Arquitectura, Fases y Diseño Técnico**  
> **Estado**: v3.0 (Versión activa y verificada) | **Tests**: 80/80 pasando (100%)

---

## 🎯 1. Visión del Proyecto

**REAL-TIME DESKTOP AGENT (RTDA)** es un **Desktop AgentOS / Agent Runtime de tiempo real para Windows 11**.

> *"RTDA no es un bot basado en screenshots. Es una capa de capacidades de escritorio persistente, event-driven y de ultra-baja latencia que permite a cualquier IA (Claude, ChatGPT, modelos locales, voz) observar y controlar la PC en tiempo real."*

```text
  SEE CONTINUOUSLY  ──►  ACT IMMEDIATELY  ──►  REASON ONLY WHEN NECESSARY
```

**Principio Fundamental:** `FAST PERCEPTION + SLOW REASONING`

---

## 🏗️ 2. Arquitectura del Sistema

```text
                           AI / AGENT CLIENTS
                       Claude / ChatGPT / Local AI
                                    │
                          MCP / WebSocket / API
                                    │
                                    ▼
                          RTDA DESKTOP SESSION
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
      CAPTURE ENGINE          INPUT ENGINE           EVENT BUS
    (WGC / DXGI 60FPS)     (Win32 SendInput <20ms) (WinEvents / SetWinEventHook)
             │                      │                      │
             ▼                      ▼                      ▼
     FRAME BUFFER (SHM)       MOUSE & KEYBOARD        EVENT STREAM
             │
             ▼
     CHANGE DETECTOR (CV)
             │
             ▼
     ROI PROCESSOR (Work Elimination)
             │
             ▼
     PERCEPTION PIPELINE (UIA / OCR / ONNX)
             │
             ▼
     UI WORLD MODEL / UI STATE
```

---

## ⚡ 3. Pilares de Rendimiento

### 1. Work Elimination (Eliminación de Trabajo)
No se analiza la pantalla completa a 60 FPS. El procesador ROI (`ROIProcessor`) acota OCR, CV y detección visual **exclusivamente a las regiones que sufrieron cambios**, descartando hasta el 95% del trabajo innecesario.

### 2. Zero-Copy Frame Transport (`SharedMemoryFrameBuffer`)
Los frames de video viajan entre procesos usando **Memoria Compartida del SO (`multiprocessing.shared_memory`)**, eliminando la necesidad de encodear en Base64 o PNG.

### 3. Native Win32 Input (`Win32SendInputBackend`)
Ejecuta clicks, movimiento de cursor, hotkeys y texto usando APIs C nativas de Windows (`user32.dll` `SendInput`) en **< 20 ms**, sin pauses o overheads de librerías externas.

### 4. Native Event Hooks (`Win32EventListener`)
Escucha cambios de foco y ventana activa nativos en tiempo real (`SetWinEventHook`), emitiendo eventos al `EventBus` sin hacer polling constante.

### 5. Sesión Persistente (`DesktopSession`)
Mantiene viva la sesión de control entre la IA y Windows durante toda la jornada de trabajo (minutos u horas) sin reinicializar captura ni controladores.

---

## 🛠️ 4. Stack Tecnológico

| Área | Tecnología | Propósito |
|---|---|---|
| Captura | `windows-capture` (DXGI/WGC) | Stream de frames de baja latencia (60 FPS) |
| UI Automation | `uiautomation` / COM nativo | Árbol de elementos de Windows |
| Computer Vision | `opencv-python`, `numpy` | Detección de cambios y ROI |
| OCR | `paddleocr` (opcional) | Lectura de texto en pantalla |
| Vision AI | ONNX Runtime / DirectML | Modelos locales de visión |
| Acciones | `Win32SendInputBackend` / `pyautogui` | Emulación de mouse y teclado de ultra-baja latencia |
| IA / Agentes | MCP + FastMCP | Interfaz estandarizada con Claude Desktop y hosts MCP |
| Datos | `pydantic` | Modelos tipados y validados |
| UI App | `PySide6` | Dashboard de escritorio |
| Tests | `pytest` | Suite de pruebas automatizadas |

---

## 📊 5. Estado de Implementación por Módulo

| Componente | Módulo | Estado | Tests |
|---|---|---|---|
| **Capture Engine** | `src/rtda/capture/` | ✅ Completado | `test_frame_buffer.py`, `test_windows_capture_lifecycle.py` |
| **Shared Memory IPC** | `src/rtda/capture/shared_memory.py` | ✅ Completado | `test_shared_memory.py` |
| **Change Detection** | `src/rtda/perception/change_detector.py` | ✅ Completado | `test_frame_change_processor.py` |
| **ROI Processor** | `src/rtda/perception/roi_processor.py` | ✅ Completado | `test_roi_processor.py` |
| **UI Automation** | `src/rtda/perception/uia.py` | ✅ Completado | `test_uia.py` |
| **Win32 SendInput** | `src/rtda/actions/win32_input.py` | ✅ Completado | `test_win32_input.py` |
| **WinEvents Hook** | `src/rtda/events/win32_listener.py` | ✅ Completado | `test_win32_listener.py` |
| **Event Bus** | `src/rtda/events/bus.py` | ✅ Completado | `test_event_bus.py` |
| **Desktop Session** | `src/rtda/session/desktop_session.py` | ✅ Completado | `test_desktop_session.py` |
| **Agent Executor** | `src/rtda/agent/executor.py` | ✅ Completado | `test_agent.py` |
| **Benchmark Framework**| `tests/benchmark/` | ✅ 25/25 (100%) | `test_benchmark.py` |
| **MCP Server (MCPB)** | `src/rtda/mcp/server.py` | ✅ Completado | `test_mcp_server.py` |

---

## 🔄 6. Fases de Desarrollo

### ✅ FASE 1 — Capture Engine
- DXGI (~5ms latencia, 60 FPS estables) y WGC (captura de ventanas específicas).
- Frame buffer configurable en memoria (`target_fps`, `max_buffer_size`, `region`, `monitor_index`).

### ✅ FASE 2 — Change Detection
- Detección de diferencias con OpenCV (`FrameChangeProcessor`).
- Muestreo de latencia y ratio de modificación de pantalla (`ProcessingMetrics`).

### ✅ FASE 3 — Windows UI Automation
- Lectura estructurada del árbol UIA (`WindowsUIAutomationInspector`).
- Normalización a `PerceptionElement` para el agente.

### ✅ FASE 4 — OCR (Opcional)
- Extracción de texto visual para elementos no expuestos por UIA (`paddleocr`).

### ✅ FASE 5 — Action Engine
- Ejecución con `Win32SendInputBackend` y guardias de seguridad (`ActionGuard`).
- Soporte para `dry_run=True` por defecto para prevenir ejecuciones accidentales.

### ✅ FASE 6 — Safety
- Clasificación de riesgo de acciones (SAFE, MODERATE, DANGEROUS) con `ActionPolicy` y `ConfirmationManager`.

### ✅ FASE 7 — Agent Loop
- Ciclo completo `OBSERVE → PLAN → ACT → VERIFY → RECOVER`.
- Detección de ventana activa con ctypes, histórico de acciones y recuperación automática (`RecoveryManager`).

### ✅ FASE 8 — MCP Server & Complemento
- Exposición de herramientas MCP estandarizadas para Claude Desktop y clientes MCP.

---

## 📐 7. Reglas de Desarrollo

### 🚫 Nunca Hacer
- Construir todo en un único archivo.
- Usar screenshots guardados en disco para el loop de ejecución.
- Enviar cada frame a una API externa de IA.
- Usar IA para detectar elementos que UIA puede leer directamente.
- Ejecutar acciones destructivas sin validación previa.
- Meter sleeps arbitrarios sin medir previamente latencias.
- Ocultar errores o ignorar métricas de telemetría.

### ✅ Siempre Hacer
- Medir latencia por fase (`observe_ms`, `plan_ms`, `execute_ms`, `verify_ms`).
- Verificar el estado post-acción antes de asumir éxito.
- Exponer `dry_run` antes de ejecutar en entornos reales.
- Documentar decisiones de diseño y testear cada módulo de forma aislada.

---

## ⏱️ 8. Métricas Objetivo y SLOs

```text
Ciclo completo observe→act:   < 500ms
UIA snapshot latencia:        < 200ms
Captura DXGI latencia:        < 10ms
Resolución de target:         < 50ms
Verificación post-acción:     < 400ms (incluye wait_ms)
```

---

## 🗺️ 9. Roadmap de Mejoras Pendientes

| Prioridad | Mejora | Descripción |
|---|---|---|
| 🔴 P1 | Telemetría extendida en `AgentTaskResult` | Registro exhaustivo de tiempos por micro-etapa |
| 🟡 P2 | Búsqueda UIA Live Dinámica | Consultar UIA en vivo si el elemento objetivo no está cacheado |
| 🟡 P2 | Integración OCR en Pipeline de Percepción | Fallback automático a OCR cuando UIA falla |
| 🟡 P2 | Detección de Diálogos / Popups | Captura preventiva de ventanas emergentes o de error |
| 🟠 P3 | Vision AI Local (ONNX) | Clasificación de elementos gráficos mediante redes locales |
| 🟠 P3 | Memoria Persistente entre Sesiones | Retención de mapa de UI entre reinicios del agente |
