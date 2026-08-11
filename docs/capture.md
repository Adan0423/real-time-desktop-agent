# Captura

## Comparacion de tecnologias

| Tecnologia | FPS esperado | Latencia | CPU | GPU | Monitor | Ventana | Complejidad | Python support | Estabilidad | Recomendacion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Windows Graphics Capture | Alto, ligado a cambios/refresh | Baja | Baja-media | Si | Si | Si | Media-alta | `windows-capture`, PyWinRT/interop | Alta en Windows 10/11 | Backend recomendado para ventana y captura consentida |
| Desktop Duplication API | Muy alto en monitor | Muy baja | Baja-media | Si | Si | No nativo | Alta | `windows-capture`, `dxcam` | Alta desde Windows 8+ | Backend inicial para monitor de baja latencia |
| DXGI directo | Muy alto | Muy baja | Baja | Si | Si | No nativo | Muy alta | Sin wrapper simple en stdlib | Alta, pero exige C++/D3D | Futuro backend nativo si necesitamos dirty/move rects completos |
| MSS | Medio | Media | Media-alta | No directo | Si | Por region/coordenadas | Baja | Excelente | Alta | Fallback/debug, no ruta principal |
| Windows Capture wrappers varios | Alto | Baja | Baja-media | Si | Depende | Depende | Baja-media | Variable | Variable | Evaluar solo si `windows-capture` falla |

## Decision

Para Fase 1 se usa una arquitectura de adaptadores:

```text
ScreenCapture
  -> WindowsCaptureEngine
       -> backend=wgc
       -> backend=dxgi
  -> FrameBuffer
  -> CaptureMetrics
  -> PySide6 Preview
```

La dependencia nueva propuesta es `windows-capture>=2.0.1` porque expone en Python tanto Windows Graphics Capture como DXGI Desktop Duplication, y su wheel actual soporta CPython 3.9+ en Windows x86-64. Esto evita escribir codigo D3D/WinRT nativo en la primera iteracion y mantiene el diseno listo para reemplazar el backend si luego necesitamos control mas fino.

`windows-capture` trae `opencv-python` como dependencia transitiva. No se agrega ningun detector OpenCV en Fase 1; se acepta temporalmente porque el wrapper resuelve captura WGC/DXGI y conversion de frames desde Python.

## Fuentes consultadas

- Microsoft Learn: Windows Graphics Capture permite adquirir frames de un display o ventana y recomienda no hacer trabajo pesado en el evento de frame.
- Microsoft Learn: Desktop Duplication entrega frames como superficies DXGI y expone dirty/move rects.
- PyPI `windows-capture`: version 2.0.1, publicada el 8 de agosto de 2026, con API Python para Graphics Capture y DXGI.
- PyPI `dxcam`: alternativa de alto rendimiento basada en Desktop Duplication con soporte CPython 3.10-3.14.
- Python MSS docs: captura por monitor o region, integrable con NumPy/OpenCV.

## Criterios de exito de Fase 1

- La app puede listar monitores.
- Puede capturar monitor completo en modo `dxgi`.
- Puede capturar monitor o ventana por titulo en modo `wgc`.
- Los frames permanecen en memoria.
- La UI muestra preview, resolucion, FPS, latencia y descartes.
- Las pruebas unitarias del buffer y metricas pasan.

## Medicion local inicial

Medido en este equipo el 2026-08-11:

| Backend | Duracion | Resolucion | Frames | FPS observado | Errores |
| --- | --- | --- | --- | --- | --- |
| DXGI | 2 s | 1366x768 | 7 | 3.42 | 0 |
| WGC | 3 s | 1366x768 | 6 | 1.88 | 0 |

El escritorio estaba casi estatico durante la medicion; estos backends entregan frames en funcion de cambios observables, por eso el FPS observado no representa un benchmark de carga con movimiento continuo.
