# Arquitectura Fase 1

## Que vamos a construir

La Fase 1 crea exclusivamente el **RTDA Capture Engine**:

- deteccion de monitores disponibles;
- seleccion de monitor;
- captura continua;
- buffer de frames en memoria;
- preview en PySide6;
- FPS, resolucion, latencia y frames descartados;
- pausa, reanudacion y parada;
- seleccion de region;
- captura de ventana por titulo cuando se usa Windows Graphics Capture.

## APIs utilizadas

La interfaz interna es `ScreenCapture`. El backend inicial es `WindowsCaptureEngine`, que puede usar:

- `wgc`: Windows Graphics Capture via `windows-capture`.
- `dxgi`: Desktop Duplication API via `windows-capture`.

La deteccion de monitores usa `EnumDisplayMonitors` y `GetMonitorInfoW` via `ctypes`, para no depender de la libreria de captura solo para listar pantallas.

## Por que

Windows Graphics Capture es el camino moderno para capturar ventana o monitor con consentimiento y sesiones de frames. Desktop Duplication/DXGI es una ruta de baja latencia y estable para captura de monitor. Mantener ambas detras de `ScreenCapture` evita acoplar el agente a una API o paquete especifico.

## Alternativas

| Opcion | Ventaja | Coste |
| --- | --- | --- |
| Windows Graphics Capture directo con PyWinRT | Control completo sobre `Direct3D11CaptureFramePool` | Mucha complejidad D3D/WinRT para el primer prototipo |
| Desktop Duplication directo con C++/ctypes | Maximo control y dirty rects | Alto coste nativo y mayor superficie de errores |
| `windows-capture` | WGC y DXGI disponibles desde Python, wheel nativa | Dependencia externa nativa |
| MSS | Muy simple y portable | Mas CPU, menos adecuado para captura continua de baja latencia |

## Como mediremos

El modulo `rtda.performance.metrics` mide:

- FPS de captura observado;
- latencia estimada entre adquisicion y push al buffer;
- frames recibidos;
- frames descartados por el buffer;
- frames perdidos estimados por intervalos largos;
- errores de backend;
- uptime.

## Archivos principales

- `src/rtda/capture/interface.py`
- `src/rtda/capture/frame.py`
- `src/rtda/capture/frame_buffer.py`
- `src/rtda/capture/windows_capture.py`
- `src/rtda/perception/interface.py`
- `src/rtda/perception/opencv_detector.py`
- `src/rtda/perception/change_detector.py`
- `src/rtda/perception/uia.py`
- `src/rtda/perception/ocr.py`
- `src/rtda/perception/vision_model.py`
- `src/rtda/actions/engine.py`
- `src/rtda/safety/action_guard.py`
- `src/rtda/agent/executor.py`
- `src/rtda/mcp/server.py`
- `src/rtda/performance/metrics.py`
- `src/rtda/app/dashboard.py`
- `src/rtda/app/main.py`
