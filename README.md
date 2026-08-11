# Real-Time Desktop Agent

![Build](https://img.shields.io/badge/build-local%20pytest-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-0.1.0-informational)
![Python](https://img.shields.io/badge/python-3.12--3.14-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/platform-Windows%2011-0078D4?logo=windows&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-compatible-6f42c1)

**Real-Time Desktop Agent (RTDA)** es un complemento local para asistentes de IA que necesitan observar y razonar sobre el escritorio en Windows 11. Su nucleo captura pantalla o ventanas, mantiene frames en memoria, mide rendimiento y expone esas capacidades por una frontera reutilizable.

El proyecto se usa de dos maneras:

- **RTDA Extension/Complement**: capa funcional para Claude Desktop, ChatGPT, Codex u otros hosts compatibles con MCP.
- **RTDA Desktop Control Surface**: app propia de escritorio para operar, visualizar y probar el complemento local con preview, metricas, overlay verde y panel IA con token.

RTDA esta pensado para desarrolladores, investigadores y builders que quieren crear agentes de escritorio locales, medir captura de baja latencia y exponer herramientas seguras a clientes de IA.

## Stack Tecnologico

| Area | Tecnologias reales |
| --- | --- |
| Frontend / UI | ![PySide6](https://img.shields.io/badge/PySide6-Qt%20UI-41CD52?logo=qt&logoColor=white) dashboard local, preview, overlay y control flotante |
| Backend / Core | ![Python](https://img.shields.io/badge/Python-3.12--3.14-3776AB?logo=python&logoColor=white) `setuptools`, arquitectura `src/` |
| Computer Vision | ![OpenCV](https://img.shields.io/badge/OpenCV-change%20detection-5C3EE8?logo=opencv&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-frames-013243?logo=numpy&logoColor=white) ![ONNX](https://img.shields.io/badge/ONNX%20Runtime-adapter-005CED) |
| Captura Windows | `windows-capture`, DXGI Desktop Duplication, Windows Graphics Capture, Win32 monitor/window APIs |
| IA / Agentes | Cliente OpenAI/Anthropic por HTTP, agente rule-based, MCP server |
| OCR | PaddleOCR/PaddlePaddle como extra opcional |
| Base de datos | No aplica actualmente |
| Infraestructura | Local-first; sin Docker ni despliegue remoto obligatorio |
| Herramientas | ![pytest](https://img.shields.io/badge/pytest-tests-0A9EDC?logo=pytest&logoColor=white) `mcp`, `pyautogui`, `uiautomation` |

## Arquitectura

```mermaid
flowchart LR
    Screen["Pantalla / Monitor / Ventana"] --> Capture["RTDA Capture Engine"]
    Capture --> Runtime["RTDA Extension Runtime"]
    Runtime --> Buffer["Frame Buffer"]
    Runtime --> Metrics["FPS / Latencia / Drops"]
    Runtime --> MCP["MCP Server / MCPB"]
    Runtime --> Desktop["Desktop Control Surface"]
    Desktop --> Preview["Preview en tiempo real"]
    Desktop --> Floating["Control flotante topmost"]
    Desktop --> Overlay["Marco verde de captura"]
    Desktop --> AIClient["Panel IA con token"]
    AIClient --> Providers["OpenAI / Anthropic"]
    MCP --> Hosts["Claude Desktop / ChatGPT / Codex / otros hosts"]
```

## Caracteristicas Principales

- Captura monitor, region o ventana especifica en Windows 11.
- Mantiene un frame buffer en memoria para consumo en tiempo real.
- Mide FPS, resolucion, latencia, frames descartados y errores.
- Muestra preview local con una interfaz de escritorio redisenada.
- Dibuja un marco verde para saber que area esta observando RTDA.
- Incluye un control flotante en segundo plano para ver estado e interactuar.
- Expone herramientas MCP para funcionar como complemento de asistentes IA.
- Permite pruebas con proveedores OpenAI/Anthropic usando token en la app.
- Mantiene acciones externas en modo seguro/dry-run mientras se endurece MVP.

## Instalacion y Uso

1. Clona el repositorio.

```powershell
git clone https://github.com/Adan0423/real-time-desktop-agent.git
cd real-time-desktop-agent
```

2. Crea y activa un entorno virtual.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instala el proyecto para captura, UI y pruebas.

```powershell
python -m pip install -e ".[capture,gui,dev]"
```

4. Ejecuta la app propia con overlay verde y flotante.

```powershell
python -m rtda.app.main
```

5. Ejecuta la app sin overlay o sin flotante.

```powershell
python -m rtda.app.main --hide-overlay
python -m rtda.app.main --hide-floating
```

6. Lista monitores detectados.

```powershell
python -m rtda.app.main --list-monitors
```

7. Ejecuta diagnostico de captura.

```powershell
python -m rtda.app.main --capture-diagnostic --duration 4 --backend dxgi --target-fps 30
```

8. Ejecuta el servidor MCP por stdio.

```powershell
python -m rtda.mcp.server --transport stdio
```

9. Ejecuta pruebas.

```powershell
python -m pytest
```

## Variables de Entorno

RTDA no carga `.env` automaticamente. Usa estas variables si integras los clientes desde Python o si tu host MCP las inyecta.

| Variable | Descripcion | Requerida |
| --- | --- | --- |
| `OPENAI_API_KEY` | Token para llamadas al proveedor OpenAI desde `AIClientConfig.from_env()` | Opcional |
| `ANTHROPIC_API_KEY` | Token para llamadas al proveedor Anthropic desde `AIClientConfig.from_env()` | Opcional |
| `RTDA_AI_PROVIDER` | Proveedor IA por defecto: `openai` o `anthropic` | Opcional |
| `RTDA_BACKEND` | Default documentado para captura (`dxgi`/`wgc`); usa `--backend` en CLI | Opcional |
| `RTDA_TARGET_FPS` | Default documentado de FPS; usa `--target-fps` en CLI | Opcional |
| `RTDA_MONITOR_INDEX` | Default documentado de monitor; usa `--monitor-index` en CLI | Opcional |

## Estructura de Carpetas

```text
real-time-desktop-agent/
|-- src/rtda/
|   |-- ai/              # Cliente OpenAI/Anthropic usado por la app propia
|   |-- app/             # CLI y dashboard PySide6
|   |-- desktop/         # Control flotante y componentes de escritorio
|   |-- extension/       # Fachada funcional que consume UI/MCP/hosts IA
|   |-- capture/         # ScreenCapture, DXGI/WGC, buffer y diagnosticos
|   |-- overlay/         # Marco verde y geometria monitor/region/ventana
|   |-- perception/      # OpenCV, UIA, OCR y vision model adapters
|   |-- actions/         # Comandos, resolucion y executor PyAutoGUI
|   |-- safety/          # Politicas de riesgo y confirmacion
|   |-- agent/           # Observe -> plan -> act -> verify -> recover
|   |-- mcp/             # Servidor MCP para Claude/hosts compatibles
|   |-- models/          # Modelos de datos Pydantic/dataclasses
|   |-- performance/     # Metricas de captura y procesamiento
|   `-- state/           # Estado observable del agente
|-- docs/                # Documentacion tecnica y roadmap
|-- tests/               # Suite pytest
|-- packaging/mcpb/      # Manifiesto base para Claude Desktop MCPB
|-- .env.example         # Variables opcionales de referencia
|-- mcpb_server.py       # Entrypoint stdio para bundle MCPB
|-- pyproject.toml       # Dependencias y metadata del paquete
`-- LICENSE              # Licencia MIT con autoria de Adan0423
```

## Roadmap / Estado

El estado por modulo vive en [docs/PROGRESS.md](docs/PROGRESS.md) y los pendientes priorizados en [docs/TODO.md](docs/TODO.md).

## Documentacion

- [Arquitectura](docs/ARCHITECTURE.md)
- [Progreso](docs/PROGRESS.md)
- [Agentes](docs/AGENTS.md)
- [Skills](docs/SKILLS.md)
- [Pendientes](docs/TODO.md)
- [Modos de uso](docs/modes.md)
- [Captura](docs/capture.md)
- [Overlay verde](docs/overlay.md)
- [IA con token](docs/ai.md)
- [MCP](docs/mcp.md)
- [Claude Desktop MCPB](docs/MCPB.md)
- [Contribuir](CONTRIBUTING.md)

## Complemento Claude Desktop

Claude Desktop instala complementos locales arrastrando un archivo `.mcpb`. `.dxt` fue el nombre anterior del formato; Anthropic recomienda `.mcpb` para paquetes nuevos.

RTDA incluye un manifiesto base en [packaging/mcpb/manifest.json](packaging/mcpb/manifest.json) y un entrypoint en [mcpb_server.py](mcpb_server.py). El empaquetado se genera con el CLI oficial `mcpb`.

```powershell
.\scripts\build_mcpb.ps1
```

Build local generada:

```text
dist/real-time-desktop-agent-0.1.0.mcpb
```

El paquete local no esta firmado; para distribucion publica conviene firmarlo y probar instalacion en Claude Desktop.

## Licencia y Contacto

Este proyecto es open source bajo licencia MIT.

Copyright (c) 2026 **Adan0423**.

Contacto configurado del proyecto: `Atrinidad.a4@gmail.com`.
