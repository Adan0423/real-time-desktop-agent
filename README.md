# 🌟 Real-Time Desktop Agent (RTDA) v3.0

[![Release](https://img.shields.io/github/v/release/Adan0423/real-time-desktop-agent?include_prereleases&color=7c3aed&label=release)](https://github.com/Adan0423/real-time-desktop-agent/releases/tag/v3.0.0-beta.1)
![Build](https://img.shields.io/badge/build-local%20pytest-brightgreen)
![Tests](https://img.shields.io/badge/tests-80%2F80%20passing-brightgreen)
![Benchmark](https://img.shields.io/badge/benchmark-100%2F100-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-3.0.0--beta.1-informational)
![Python](https://img.shields.io/badge/python-3.12--3.14-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/platform-Windows%2011-0078D4?logo=windows&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-compatible-6f42c1)

> **Real-Time Desktop Agent (RTDA)** es un **Desktop AgentOS / Agent Runtime de tiempo real v3.0 para Windows 11**.
> Transforma la interacción de la IA con la PC: pasa de ser un "bot rudimentario de screenshots" a ser una **capa de capacidades de escritorio persistente, event-driven y de ultra-baja latencia**.

```text
  SEE CONTINUOUSLY  ──►  ACT IMMEDIATELY  ──►  REASON ONLY WHEN NECESSARY
```

---

## 🛠️ Stack Tecnológico Completo

| Área | Tecnologías & Componentes |
|---|---|
| 🪟 **Kernel & Control Nativo** | Windows 11 API, **Native Win32 `SendInput`** (`<15ms` latencia de input), **WinEvents Hook (`SetWinEventHook`)**, Windows UI Automation (`uiautomation`). |
| 🎥 **Captura & Buffer** | `windows-capture`, DXGI Desktop Duplication, Windows Graphics Capture (WGC), **`SharedMemory` IPC Zero-Copy Frame Buffer** (`multiprocessing.shared_memory`). |
| 👁️ **Visión & Percepción** | OpenCV 4 (`opencv-python`), **`ROIProcessor` (Work Elimination: >93% ahorro de cómputo)**, ONNX Runtime, NumPy 2.0. |
| 🧠 **Runtime & Sesión IA** | **`DesktopSession`** (sesión persistente de control), `AgentObserver`, `RuleBasedPlanner`, `Verifier` (diff UIA real), `RecoveryManager`. |
| 🌐 **Servicio & Gateway** | **FastAPI** (REST Administrative Gateway), **WebSockets** (Real-time Event Stream `/events` y `/desktop` Data Channel). |
| 🔌 **Protocolos & IA** | **Model Context Protocol (`MCP` v1.27)**, FastMCP, **`.mcpb` 1-Click Extension Bundle**, Cliente Multi-Proveedor HTTP (Claude, OpenAI, Groq, OpenRouter, NVIDIA). |
| 📊 **Testing & Benchmark** | `pytest`, **Suite de Evaluación Automatizada de 25 Casos de Prueba (100% éxito, Score 100/100)**, 80/80 Pruebas unitarias e integración. |
| 🖥️ **Dashboard & UI** | PySide6 (Qt) Dashboard local, Panel de Vista Previa, Control Flotante Topmost, Marco Verde (Overlay). |

---

## 🏗️ Arquitectura del Sistema

```text
                           CLIENTES IA
                   Claude / ChatGPT / Local AI / Voz
                                  │
                        MCP / WebSocket / API
                                  │
                                  ▼
                        RTDA DESKTOP SESSION
                                  │
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                      ▼
    CAPTURE ENGINE          INPUT ENGINE           EVENT BUS
  (WGC / DXGI 60FPS)     (Win32 SendInput <15ms) (WinEvents / SetWinEventHook)
           │                      │                      │
           ▼                      ▼                      ▼
   FRAME BUFFER (SHM)       MOUSE & KEYBOARD        EVENT STREAM
           │
           ▼
   CHANGE DETECTOR (CV)
           │
           ▼
   ROI PROCESSOR (Work Elimination >93%)
           │
           ▼
   PERCEPTION PIPELINE (UIA / OCR / ONNX)
           │
           ▼
   UI WORLD MODEL / UI STATE
```

---

## ✨ Características Principales & Innovaciones

- ⚡ **Native Win32 `SendInput` Execution**: Clicks de mouse, pulsaciones de teclado y hotkeys en **< 15 ms** sin delays artificiales.
- 🔲 **Work Elimination (`ROIProcessor`)**: Recorta las imágenes solo a las regiones modificadas (`ROI`), reduciendo el uso de CPU/GPU en más del 93% en frames sin cambio.
- 🚀 **Zero-Copy IPC Frame Buffer (`SharedMemoryFrameBuffer`)**: Transporta frames crudos BGRA entre procesos por memoria compartida sin serialización Base64/PNG.
- 🔔 **Native WinEvents Listener (`SetWinEventHook`)**: Escucha cambios de foco y ventana activa nativos en tiempo real sin polling.
- 💼 **Sesión Persistente (`DesktopSession`)**: Mantiene viva la sesión de control entre la IA y Windows durante toda la jornada de trabajo.
- 🌐 **Service Gateway & WebSockets**: Expone endpoints REST (`/health`, `/metrics`, `/sessions`) y streaming WebSocket (`/events` y `/desktop`).
- 🎯 **25-Case Benchmark Suite**: Evaluado en 4 niveles de dificultad (Single Actions, Multi-Step, Multi-Window, Complex Workflows) con **100% de éxito**.
- 📦 **MCP Bundle (`.mcpb`) 1-Click**: Instalación inmediata de 1 click para Claude Desktop.

---

## 🚀 Guía de Instalación y Distribución

> Consulta la [**Guía Completa de Instalación y Distribución (docs/INSTALLATION.md)**](docs/INSTALLATION.md) para ver las instrucciones detalladas con capturas e iconos.

| Método | Cliente Destino | Tipo de Instalación | Instrucciones Rápidas |
|---|---|---|---|
| 🟣 **Método A** | **Claude Desktop** | **1-Click MCP Bundle (`.mcpb`)** | Descargar [`v3.0.0-beta.1 Release`](https://github.com/Adan0423/real-time-desktop-agent/releases/tag/v3.0.0-beta.1) e instalar `.mcpb` en Claude. |
| 🔵 **Método B** | **Cursor / VSCode / Dev** | **`pip` Direct Wheel Install** | `pip install https://github.com/Adan0423/real-time-desktop-agent/releases/download/v3.0.0-beta.1/real_time_desktop_agent-3.0.0b1-py3-none-any.whl` |
| 🔴 **Método C** | **ChatGPT / API / WebSocket** | **Servidor SSE / WebSocket** | `python -m rtda.mcp.server --transport sse` |

---

## 💻 Comandos de Desarrollo y Uso

### 1. Clonar e instalar entorno
```powershell
git clone https://github.com/Adan0423/real-time-desktop-agent.git
cd real-time-desktop-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install uv
uv pip install -e ".[capture,gui,dev,service]"
```

### 2. Ejecutar la App de Control de Escritorio (Dashboard + Overlay + Flotante)
```powershell
python -m desktop.main
```

### 3. Ejecutar el Servidor MCP (STDIO para Claude)
```powershell
python -m rtda.mcp.server --transport stdio
```

### 4. Ejecutar la Suite de Pruebas Automatizadas (80 Tests)
```powershell
python -m pytest tests/ -v
```

### 5. Ejecutar la Suite de Benchmark Automatizada (25 Casos)
```powershell
python -m pytest tests/unit/test_benchmark.py -v
```

### 6. Empaquetar la Extensión MCPB para Claude Desktop
```powershell
.\scripts\build_mcpb.ps1
```

---

## 📊 Cobertura y Benchmark de Rendimiento

```text
======================= BENCHMARK SUITE RESULTS =======================
Total Tests: 25 | Passed: 25 | Failed: 0 | Pass Rate: 100.0%
Overall Score: 100.0 / 100.0 | Avg Task Latency: ~2.5 ms

Level Breakdown:
  • Level 1: Single Actions         ──► 100.0 / 100
  • Level 2: Multi-Step             ──► 100.0 / 100
  • Level 3: Multi-Window           ──► 100.0 / 100
  • Level 4: Complex Workflows      ──► 100.0 / 100
=======================================================================
```

---

## 📁 Estructura del Proyecto

```text
real-time-desktop-agent/
├── .github/
│   ├── workflows/       # CI/CD Workflows (ci.yml, release.yml)
│   ├── dependabot.yml   # Actualización de dependencias
│   └── PULL_REQUEST_TEMPLATE.md
├── src/rtda/
│   ├── actions/         # Native Win32 SendInput & ActionEngine
│   ├── agent/           # AgentExecutor loop, RuleBasedPlanner & Verifier
│   ├── capture/         # DXGI/WGC, Frame Buffer & SharedMemory IPC
│   ├── complement/      # API de complemento RTDA
│   ├── events/          # EventBus & Native Win32 SetWinEventHook Listener
│   ├── mcp/             # MCP Server (7 herramientas expuestas)
│   ├── perception/      # OpenCV, ROIProcessor, UIA Inspector & Vision ONNX
│   ├── safety/          # ActionGuard & políticas de seguridad
│   ├── service/         # FastAPI Administrative Gateway & WebSockets
│   └── session/         # DesktopSession persistente
├── desktop/             # App de escritorio PySide6 (Dashboard, Overlay, Floating)
├── docs/                # Documentación técnica, arquitectura e instalación
│   ├── plans/           # Planes de arquitectura (MASTER_PLAN, v2, v3)
│   ├── INSTALLATION.md  # Guía detallada de instalación 3 métodos
│   └── PROGRESS.md      # Reporte completo de progreso por fases
├── tests/               # Suite de 80 pruebas unitarias, integración y benchmark
│   ├── unit/            # Pruebas unitarias
│   ├── capture/         # Pruebas de captura y memoria compartida
│   ├── perception/      # Pruebas de OpenCV, ROI y UIA
│   ├── ui/              # Pruebas de interfaz PySide6
│   └── benchmark/       # Framework y 25 casos de benchmark
├── dist/                # Paquete distribuible (.mcpb)
├── CHANGELOG.md         # Historial de cambios
├── pyproject.toml       # Configuración y dependencias del paquete
└── LICENSE              # Licencia MIT (Adan0423)
```

---

## 📚 Documentación Técnica Adicional

- [📘 **Guía de Instalación y Distribución**](docs/INSTALLATION.md)
- [🌟 **Master Plan Arquitectónico v3.0**](docs/plans/MASTER_PLAN.md)
- [📊 **Reporte de Progreso y KPIs**](docs/PROGRESS.md)
- [📜 **Historial de Cambios (Changelog)**](CHANGELOG.md)
- [🏗️ **Documentación de Arquitectura**](docs/ARCHITECTURE.md)
- [🔌 **Documentación de MCP**](docs/mcp.md)
