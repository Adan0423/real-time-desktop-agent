# Perception

## Fase 2: OpenCV Change Detection

La Fase 2 agrega deteccion local de cambios entre frames consecutivos. No interpreta elementos de UI, no hace OCR y no llama modelos de IA. Su unica responsabilidad es responder rapido:

```text
previous frame + latest frame
  -> grayscale
  -> absdiff
  -> threshold
  -> morphology
  -> contours
  -> changed regions
```

## API usada

- `cv2.cvtColor`: convertir BGRA/BGR a gris.
- `cv2.absdiff`: calcular diferencia absoluta pixel a pixel.
- `cv2.threshold`: convertir la diferencia en mascara binaria.
- `cv2.morphologyEx` y `cv2.dilate`: reducir ruido y consolidar regiones.
- `cv2.findContours`: extraer regiones conectadas.

OpenCV recomienda usar imagenes binarias antes de buscar contornos; por eso el detector siempre aplica umbral antes de `findContours`.

## Decisiones

| Opcion | Latencia | CPU | GPU | Complejidad | Estabilidad | Mantenibilidad |
| --- | --- | --- | --- | --- | --- | --- |
| AbsDiff + threshold + contours | Baja | Baja-media | No | Baja | Alta | Alta |
| SSIM | Media | Media | No | Media | Alta | Media |
| Perceptual hash | Baja | Baja | No | Baja | Alta | Baja para localizar regiones |
| Dirty rects nativos DXGI/WGC | Muy baja | Baja | Si | Alta | Alta | Media |

La recomendacion inicial es `absdiff + threshold + contours` porque entrega bounding boxes accionables, se prueba facil con arrays sinteticos y mantiene Fase 2 independiente del backend de captura. Dirty rects queda como optimizacion posterior del backend.

El detector trabaja por defecto con `downscale=0.5` para reducir latencia en frames completos. Los bounding boxes se reescalan al tamano original del frame. Con frames reales aislados de `1366x768`, la medicion local quedo alrededor de `5.8 ms` despues del warmup.

## Salida estructurada

El detector devuelve `ChangeDetectionResult`:

- `changed`: si hubo cambio significativo.
- `regions`: regiones `BoundingBox` ordenadas por area descendente.
- `changed_pixels`: pixeles no cero en la mascara procesada.
- `changed_ratio`: proporcion de cambio en la mascara.
- `latency_ms`: tiempo local de OpenCV.

## Medicion

`ProcessingMetrics` registra:

- `processing_fps`
- `opencv_latency_ms`
- `frames_processed`
- `changed_frames`
- `latest_changed_regions`
- `latest_changed_ratio`

## Fase 3: UIA como percepcion estructurada

UIA complementa OpenCV: OpenCV dice donde cambio la imagen; UIA dice que controles existen, como se llaman y donde estan. Esta fase no hace clicks ni escribe texto; solo observa.

El snapshot UIA devuelve `UIASnapshot` con elementos `UIAElement` y se puede convertir a `PerceptionElement` con `source="uia"` para la futura fusion UIA/OCR/OpenCV/Vision AI.
