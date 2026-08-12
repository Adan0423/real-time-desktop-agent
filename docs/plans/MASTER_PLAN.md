# 🌟 MASTER PLAN v3.0 — REAL-TIME DESKTOP AGENT

> **Documento Maestro de Arquitectura y Diseño Técnico**
> **Estado**: v3.0 (Versión activa y verificada) | **Tests**: 80/80 pasando (100%)

---

## 🎯 1. Visión del Proyecto

**REAL-TIME DESKTOP AGENT (RTDA)** es un **Desktop AgentOS / Agent Runtime de tiempo real para Windows 11**.

> *"RTDA no es un bot basado en screenshots. Es una capa de capacidades de escritorio persistente, event-driven y de ultra-baja latencia que permite a cualquier IA (Claude, ChatGPT, modelos locales, voz) observar y controlar la PC en tiempo real."*

```text
  SEE CONTINUOUSLY  ──►  ACT IMMEDIATELY  ──►  REASON ONLY WHEN NECESSARY
```

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

## 📊 4. Estado de Implementación de Componentes

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
