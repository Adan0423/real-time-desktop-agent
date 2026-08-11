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

## Regla de diseno

La captura favorece `latest_frame` sobre procesar todos los frames. Si el consumidor se retrasa, el buffer descarta los frames antiguos y conserva el estado visual mas reciente.

## Medicion inicial

Para medir sin UI:

```powershell
python -m rtda.app.main --headless --duration 5 --backend dxgi --target-fps 60
```

El resultado esperado es una linea JSON con el snapshot de metricas.

## Resultado local inicial

La validacion headless con DXGI fuera del sandbox produjo captura real a `1366x768`, sin errores de backend. El FPS observado fue bajo porque no habia movimiento continuo en pantalla; para benchmark de rendimiento real se debe repetir con contenido animado o una ventana que invalide frames constantemente.
