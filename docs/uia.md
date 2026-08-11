# Windows UI Automation

## Fase 3

La Fase 3 agrega inspeccion de Windows UI Automation como fuente estructurada de percepcion. No ejecuta acciones.

```text
Windows UIA
  -> root/window control
  -> bounded tree traversal
  -> UIAElement[]
  -> PerceptionElement(source="uia")
```

## API usada

Se usa `uiautomation`, que envuelve Microsoft UI Automation sobre COM. Las propiedades leidas coinciden con la especificacion de UIA:

- `Name`
- `ControlTypeName`
- `BoundingRectangle`
- `IsEnabled`
- `IsOffscreen`
- `AutomationId`
- `ClassName`
- `ProcessId`
- `NativeWindowHandle`

La traversal es acotada por `max_depth` y `max_elements` para evitar bloquear el loop de percepcion en arboles grandes.

Por defecto tambien se filtran elementos cuyo `BoundingRectangle` cae fuera del rectangulo raiz con un margen pequeno. Esto evita incluir ventanas auxiliares de sistema con coordenadas como `-32000,-32000`.

## Decisiones

| Opcion | Latencia | CPU | Complejidad | Estabilidad | Mantenibilidad |
| --- | --- | --- | --- | --- | --- |
| `uiautomation` | Baja-media | Baja | Baja | Alta | Alta |
| COM directo con `comtypes` | Baja | Baja | Alta | Alta | Media |
| `pywinauto` | Media | Media | Media | Alta | Media |
| OCR como fuente primaria | Media-alta | Media-alta | Media | Variable | Baja para controles |

Recomendacion: `uiautomation` para Fase 3 porque ya esta instalado, usa UIA real y nos permite avanzar con una interfaz propia (`UIAutomationInspector`) que luego puede cambiar de backend.

## Medicion

Se registra:

- `uia_latency_ms`
- `uia_snapshots`
- `latest_uia_elements`

Ejemplo:

```powershell
python -m rtda.app.main --headless --duration 0 --inspect-uia --uia-max-depth 3
```

En la UI de debugging, el boton `Inspect UIA` ejecuta un snapshot manual. No corre cada frame porque UIA puede tardar cientos de milisegundos en arboles reales.

## Limitaciones

Algunas aplicaciones no exponen todo por UIA, o exponen nombres vacios. Por eso UIA no sera la unica fuente: se fusionara con OCR, OpenCV y Vision AI en fases posteriores.
