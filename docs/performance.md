# Performance

## Metricas Fase 1

| Metrica | Definicion |
| --- | --- |
| `capture_fps` | Frames recibidos por segundo en una ventana movil |
| `capture_latency_ms` | Tiempo entre timestamp de adquisicion disponible y recepcion local |
| `frames_captured` | Total de frames empujados al pipeline RTDA |
| `buffer_dropped_frames` | Frames descartados por limite del ring buffer |
| `estimated_missed_frames` | Frames esperados pero no observados por intervalos largos |
| `backend_errors` | Errores reportados por el adaptador nativo |
| `uptime_s` | Tiempo activo de la sesion |
| `processing_fps` | Pares de frames procesados por segundo |
| `opencv_latency_ms` | Tiempo local del detector OpenCV |
| `changed_frames` | Frames procesados donde se detecto cambio significativo |
| `latest_changed_regions` | Cantidad de regiones detectadas en el ultimo procesamiento |
| `latest_changed_ratio` | Proporcion de pixeles cambiados en la ultima mascara |
| `uia_latency_ms` | Tiempo de snapshot UIA |
| `uia_snapshots` | Cantidad de snapshots UIA realizados |
| `latest_uia_elements` | Elementos UIA del ultimo snapshot |
| `ocr_latency_ms` | Tiempo de OCR local |
| `vision_ai_latency_ms` | Tiempo de llamada vision model |
| `action_latency_ms` | Tiempo de resolucion/ejecucion de accion |
| `ocr_runs` | Cantidad de corridas OCR |
| `vision_ai_calls` | Cantidad de llamadas Vision AI |
| `actions_executed` | Acciones procesadas por el action engine |

## Regla de diseno

La captura favorece `latest_frame` sobre procesar todos los frames. Si el consumidor se retrasa, el buffer descarta los frames antiguos y conserva el estado visual mas reciente.

## Medicion inicial

Para medir sin UI:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60
```

El resultado esperado es una linea JSON con el snapshot de metricas.

Para incluir Fase 2:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60 --detect-changes
```

Para incluir Fase 3 sin captura:

```powershell
python -m rtda.app.main --headless --duration 0 --inspect-uia --uia-max-depth 3
```

## Resultado local inicial

La validacion headless con DXGI fuera del sandbox produjo captura real a `1366x768`, sin errores de backend. El FPS observado fue bajo porque no habia movimiento continuo en pantalla; para benchmark de rendimiento real se debe repetir con contenido animado o una ventana que invalide frames constantemente.

Fase 2 medida con frames reales aislados de `1366x768`: OpenCV quedo cerca de `5.8 ms` despues del warmup con `downscale=0.5`.

Fase 3 medida con `--inspect-uia --uia-max-depth 2`: snapshot UIA de escritorio con 10 elementos utiles, 0 errores y aproximadamente `663 ms`. UIA debe ejecutarse bajo demanda o como respuesta a cambios, no por frame.
