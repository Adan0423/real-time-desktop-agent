# REAL-TIME DESKTOP AGENT

Proyecto inicial para construir un agente de escritorio en Windows 11 con percepcion rapida, razonamiento lento y metricas desde el primer modulo.

Estado actual: **Fase 1 - RTDA Capture Engine**.

## Fase 1

Objetivo implementado en esta base:

```text
SCREEN
  -> LOW-LATENCY CAPTURE
  -> FRAME BUFFER
  -> REAL-TIME PREVIEW
  -> FPS / LATENCY METRICS
```

No incluye OCR, OpenCV, UI Automation, Vision AI, mouse ni teclado.

## Dependencias

Dependencias minimas del nucleo:

- `numpy`: representacion de frames en memoria.

Dependencias opcionales para ejecutar captura y preview:

- `windows-capture`: adaptador nativo Python/Rust para Windows Graphics Capture y DXGI Desktop Duplication.
- `PySide6`: interfaz grafica local para preview y metricas.
- `pytest`: pruebas del nucleo.

Nota: `windows-capture` instala `opencv-python` como dependencia transitiva. En esta fase no hay pipeline OpenCV propio; solo queda disponible porque el wrapper nativo lo declara.

Instalacion recomendada:

```powershell
python -m pip install -e ".[capture,gui,dev]"
```

## Uso

Ejecutar la interfaz de debugging:

```powershell
python -m rtda.app.main
```

Ejecutar captura en consola durante cinco segundos:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60
```

Ejecutar pruebas:

```powershell
python -m pytest
```

## Documentacion

- [Arquitectura](docs/architecture.md)
- [Captura](docs/capture.md)
- [Performance](docs/performance.md)

El prompt maestro original queda como especificacion de producto en `PROMPT MAESTRO — REAL-TIME DESKTOP AGENT.md`.
