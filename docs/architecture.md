# Arquitectura

Ultima actualizacion: 2026-08-11

## Vision General

RTDA es una aplicacion local-first para Windows 11. Su nucleo captura pantalla,
mantiene frames recientes en memoria, mide rendimiento y expone la observacion a
dos superficies:

- app propia con preview, overlay verde y panel IA;
- servidor MCP para Claude Desktop, ChatGPT u otros hosts compatibles.

## Diagrama General

```mermaid
flowchart TD
    Input["Monitor / Region / Ventana"] --> Capture["WindowsCaptureEngine"]
    Capture --> Buffer["FrameBuffer"]
    Capture --> Metrics["CaptureMetrics"]
    Capture --> Overlay["GreenCaptureOverlay"]
    Buffer --> Preview["Dashboard PySide6"]
    Buffer --> Change["OpenCV Change Detection"]
    Input --> UIA["Windows UI Automation"]
    Buffer --> OCR["PaddleOCR Adapter"]
    Buffer --> Vision["ONNX / Structured Vision"]
    Change --> State["UIState"]
    UIA --> State
    OCR --> State
    Vision --> State
    State --> Planner["RuleBasedPlanner"]
    Planner --> Guard["ActionGuard"]
    Guard --> Executor["PyAutoGUI / Dry Run"]
    State --> MCP["MCP Server"]
    MCP --> Hosts["Claude Desktop / otros clientes MCP"]
    Preview --> AI["AIClient"]
    AI --> Providers["OpenAI / Anthropic"]
```

## Decisiones Tecnicas

| Decision | Eleccion | Motivo |
| --- | --- | --- |
| Captura de monitor | DXGI Desktop Duplication via `windows-capture` | Baja latencia y buena estabilidad para escritorio Windows |
| Captura de ventana | Windows Graphics Capture via `windows-capture` | Soporta ventana especifica cuando Windows lo permite |
| Enumeracion de monitores | Win32 `EnumDisplayMonitors` / `GetMonitorInfoW` via `ctypes` | Evita depender del backend de captura para listar pantallas |
| UI local | PySide6 | Permite preview, controles y overlay sin navegador |
| Overlay verde | QWidget transparente topmost | Da feedback visual inmediato de que area observa RTDA |
| Change detection | OpenCV + NumPy | Rapido, local y medible para diferencias entre frames |
| UI Automation | `uiautomation` | Lectura estructurada de controles Windows sin OCR |
| OCR | PaddleOCR opcional | Adapter listo, pero depende de entorno compatible |
| Vision local | ONNX Runtime adapter | Prepara una ruta para modelos locales sin fijar arquitectura aun |
| Acciones | PyAutoGUI detras de `ActionGuard` | Mantiene una frontera de seguridad y permite dry-run |
| Integracion externa | MCP | Protocolo estandar para que hosts IA consuman tools locales |
| IA app propia | HTTP stdlib hacia OpenAI/Anthropic | Evita SDKs extra y facilita pruebas con transporte fake |

## Flujo de Captura

```mermaid
sequenceDiagram
    participant User as Usuario
    participant App as RTDA App
    participant Capture as WindowsCaptureEngine
    participant Buffer as FrameBuffer
    participant UI as Preview/Metricas
    User->>App: start monitor/region/window
    App->>Capture: start()
    Capture->>Capture: DXGI o WGC frame callback
    Capture->>Buffer: push(Frame)
    Capture->>UI: metrics()
    UI->>Buffer: latest_frame()
    UI->>User: preview + FPS + latencia + drops
```

## Flujo MCP

```mermaid
sequenceDiagram
    participant Host as Claude/Host MCP
    participant MCP as rtda.mcp.server
    participant Capture as Capture Engine
    participant Safety as ActionGuard
    Host->>MCP: capture_monitors()
    MCP->>Capture: list_monitors()
    Capture-->>MCP: MonitorInfo[]
    MCP-->>Host: JSON
    Host->>MCP: dry_run_action(click, target)
    MCP->>Safety: classify + resolve
    Safety-->>MCP: dry_run result
    MCP-->>Host: JSON
```

## Fronteras de Seguridad

- MCP no ejecuta acciones reales: expone `dry_run_action`.
- `ActionGuard` clasifica acciones en `safe`, `moderate` y `dangerous`.
- Acciones destructivas como `delete`, `publish`, `send`, `purchase` y `submit`
  se tratan como peligrosas.
- El panel IA no recibe frames todavia; usa prompt y contexto textual de
  metricas.

## Limitaciones Actuales

- No hay base de datos persistente.
- No hay CI/CD ni empaquetado release automatizado.
- El OCR real depende de una version de Python compatible con PaddlePaddle.
- El MCPB tiene manifiesto base, pero el paquete `.mcpb` final debe validarse
  con el CLI oficial `mcpb`.
- La vision multimodal hacia OpenAI/Anthropic todavia no envia imagen/frame.
