# REAL-TIME DESKTOP AGENT

Proyecto inicial para construir un agente de escritorio en Windows 11 con percepcion rapida, razonamiento lento y metricas desde el primer modulo.

Estado actual: **Fase 8 + modos de integracion** sobre captura, percepcion, acciones seguras, agente, app propia y complemento MCP.

## Fases implementadas

Fase 1:

```text
SCREEN
  -> LOW-LATENCY CAPTURE
  -> FRAME BUFFER
  -> REAL-TIME PREVIEW
  -> FPS / LATENCY METRICS
```

Fase 2:

```text
FRAME BUFFER
  -> PREVIOUS / LATEST FRAME
  -> OPENCV CHANGE DETECTION
  -> CHANGED REGIONS + PROCESSING METRICS
```

Fase 3:

```text
WINDOWS UI AUTOMATION
  -> UI TREE SNAPSHOT
  -> STRUCTURED ELEMENTS
  -> BOUNDING BOXES + UIA METRICS
```

Fase 4:

```text
FRAME / REGION
  -> PADDLEOCR ADAPTER
  -> TEXT ELEMENTS
```

Fase 5:

```text
SEMANTIC ACTION
  -> SAFETY GUARD
  -> TARGET RESOLVER
  -> PYAUTOGUI EXECUTOR
```

Fase 6:

```text
VISION MODEL INTERFACE
  -> ONNX RUNTIME ADAPTER
  -> STRUCTURED VISION STUB
```

Fase 7:

```text
OBSERVE -> PLAN -> ACT -> VERIFY -> RECOVER
```

Fase 8:

```text
MCP SERVER
  -> health / inspect_uia / plan_goal / classify_action / dry_run_action
```

## Dependencias

Dependencias minimas del nucleo:

- `numpy`: representacion de frames en memoria.
- `opencv-python`: deteccion local de cambios en Fase 2.
- `uiautomation`: lectura estructurada de Windows UI Automation en Fase 3.
- `pyautogui`: backend inicial de mouse/teclado en Fase 5.
- `onnxruntime`: adaptador para modelos locales en Fase 6.
- `mcp`: servidor de herramientas en Fase 8.

Dependencias opcionales para ejecutar captura y preview:

- `windows-capture`: adaptador nativo Python/Rust para Windows Graphics Capture y DXGI Desktop Duplication.
- `PySide6`: interfaz grafica local para preview y metricas.
- `pytest`: pruebas del nucleo.

Nota: `windows-capture` tambien instala `opencv-python` como dependencia transitiva. Lo declaramos de forma explicita porque Fase 2 ya usa OpenCV directamente.

Nota OCR: PaddleOCR/PaddlePaddle no tiene wheel disponible para el Python 3.14 de este entorno. El adaptador esta implementado y probado con cliente fake; OCR real debe ejecutarse en un entorno Python compatible con PaddlePaddle.

Instalacion recomendada:

```powershell
python -m pip install -e ".[capture,gui,dev]"
```

## Uso

El proyecto se puede usar de dos maneras:

1. **App propia RTDA**: interfaz local para capturar pantalla, ver preview,
   marcar el area capturada con borde verde y probar IA con token.
2. **Complemento para IA externa**: servidor MCP para hosts compatibles
   como clientes de ChatGPT, Claude u otros agentes que puedan llamar tools.

Ejecutar la interfaz de captura de Fase 1:

```powershell
python -m rtda.app.main
```

Por defecto la UI muestra el borde verde del area capturada. Para ocultarlo:

```powershell
python -m rtda.app.main --hide-overlay
```

La interfaz tambien incluye un panel IA para pruebas con token. El token se usa
en memoria y no se escribe en el repositorio.

Por defecto las herramientas de percepcion de fases posteriores quedan ocultas
para mantener aislado el Primer Objetivo.

Ejecutar la interfaz de debugging con herramientas de percepcion/UIA:

```powershell
python -m rtda.app.main --enable-perception-tools
```

Ejecutar captura en consola durante cinco segundos:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60
```

Listar monitores:

```powershell
python -m rtda.app.main --list-monitors
```

Validar el Primer Objetivo:

```powershell
python -m rtda.app.main --capture-diagnostic --duration 4 --backend dxgi --target-fps 30
```

Ejecutar captura con deteccion de cambios:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60 --detect-changes
```

Inspeccionar UIA en consola:

```powershell
python -m rtda.app.main --headless --duration 0 --inspect-uia --uia-max-depth 3
```

Ejecutar servidor MCP por stdio:

```powershell
python -m rtda.mcp.server --transport stdio
```

Ejecutar pruebas:

```powershell
python -m pytest
```

## Documentacion

- [Arquitectura](docs/architecture.md)
- [Modos de uso](docs/modes.md)
- [Captura](docs/capture.md)
- [Overlay verde](docs/overlay.md)
- [IA con token](docs/ai.md)
- [Percepcion](docs/perception.md)
- [UI Automation](docs/uia.md)
- [OCR](docs/ocr.md)
- [Acciones](docs/actions.md)
- [Seguridad](docs/safety.md)
- [Vision](docs/vision.md)
- [Agente](docs/agent.md)
- [MCP](docs/mcp.md)
- [Performance](docs/performance.md)

El prompt maestro original queda como especificacion de producto en `PROMPT-AGENT.md`.
