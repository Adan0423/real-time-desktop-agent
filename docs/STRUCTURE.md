# Estructura para desarrolladores

Ultima actualizacion: 2026-08-11

## Regla principal

`real-time-desktop-agent` es el complemento completo. La interfaz de escritorio
es una forma de consumirlo, no el centro de la arquitectura.

```text
rtda.complement  -> API publica del complemento IA
desktop/         -> UI propia, dashboard y flotante
rtda.app         -> launchers CLI y compatibilidad
rtda.mcp         -> transporte para hosts IA externos
```

## Mapa de carpetas

| Carpeta | Que contiene | Puede depender de |
| --- | --- | --- |
| `src/rtda/complement/` | Fachada principal para captura, vision, mouse, teclado y border | `capture`, `perception`, `actions`, `overlay`, `safety` |
| `src/rtda/capture/` | ScreenCapture, DXGI/WGC, frame buffer, monitores y diagnosticos | `performance`, `models` |
| `src/rtda/perception/` | OpenCV, UIA, OCR y vision model adapters | `capture`, `models`, `performance` |
| `src/rtda/actions/` | Mouse, teclado, scroll, resolver y executor PyAutoGUI | `models`, `safety` |
| `src/rtda/overlay/` | Marco verde y geometria del area observada | `capture` |
| `src/rtda/mcp/` | Tools MCP para Claude/ChatGPT/Codex y otros hosts | `complement` o modulos core |
| `desktop/` | App PySide6 independiente: dashboard, floating y modulos UI | `src/rtda/complement`, `src/rtda/ai` |
| `src/rtda/app/` | CLI launchers y shims antiguos | `desktop`, `capture`, `mcp` |
| `src/rtda/extension/` | Compatibilidad hacia `rtda.complement` | `complement` |
| `plugins/real-time-desktop-agent/` | Plugin local ChatGPT/Codex | MCP server de `src/rtda` |
| `.agents/plugins/` | Marketplace local para ChatGPT Desktop/Codex | `plugins/` |

## API recomendada

Los desarrolladores que integran RTDA deben empezar por:

```python
from rtda.complement import RTDAComplementRuntime
from rtda.capture.interface import CaptureConfig

runtime = RTDAComplementRuntime(CaptureConfig(backend="dxgi", target_fps=60))
runtime.start_capture()
observation = runtime.observe()
runtime.click("Guardar")
runtime.hotkey("ctrl", "l")
runtime.stop_capture()
```

Para activar el marco verde desde el complemento:

```python
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.capture.interface import CaptureConfig

runtime = RTDAComplementRuntime(
    RTDAComplementConfig(
        capture=CaptureConfig(backend="dxgi"),
        enable_border=True,
    )
)
runtime.start_capture()
runtime.refresh_border()
```

## Reglas de contribucion tecnica

- Agrega capacidades reutilizables en `rtda.complement` o en modulos core, no en
  `desktop/`.
- La UI puede consumir el complemento, pero el complemento no debe depender de
  widgets del dashboard.
- Mantener mouse/teclado detras de `ActionGuard` y `PyAutoGUIActionExecutor`.
- Mantener el border como capacidad opcional; procesos headless no deben crear
  Qt automaticamente salvo que `enable_border=True`.
- Cualquier feature nueva debe tener una prueba de runtime o de modulo core.
- `rtda.extension` queda solo para compatibilidad; nuevos imports deben usar
  `rtda.complement`.

## Estructura desktop

```text
desktop/
|-- main.py             # launcher CLI de la app propia
|-- dashboard.py        # orquestador de ventana y senales Qt
|-- runtime_bridge.py   # consumo desktop del complemento RTDA
|-- ai_bridge.py        # llamadas IA manuales en background
|-- floating.py         # control flotante compacto
|-- theme.py            # QSS centralizado
`-- ui/
    |-- sidebar.py      # rail izquierdo y paginas Captura/Metricas/IA/Config
    |-- target_panel.py # monitor, backend y region
    |-- runtime_panel.py # botones y metricas
    |-- settings_panel.py # preferencias visuales/runtime del desktop
    |-- ai_panel.py     # prueba manual con token
    |-- panels.py       # exports compatibles
    |-- preview.py      # superficie de preview realtime
    |-- widgets.py      # piezas reutilizables compactas
    `-- floating_widgets.py
```

Regla: `desktop/` puede importar `rtda.complement`; `src/rtda/` no debe importar
`desktop/`.
