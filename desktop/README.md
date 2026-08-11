# RTDA Desktop

Esta carpeta contiene la app de escritorio separada del complemento
`real-time-desktop-agent`.

La carpeta `src/rtda/` es el complemento/core para IA. Esta carpeta `desktop/`
es solo la interfaz propia para probar y controlar ese complemento:

- `dashboard.py`: ventana principal PySide6.
- `runtime_bridge.py`: adaptador desktop hacia `RTDAComplementRuntime`.
- `ai_bridge.py`: llamadas IA manuales fuera del event loop Qt.
- `floating.py`: control flotante compacto en segundo plano.
- `theme.py`: stylesheet central del dashboard.
- `ui/`: sidebar, paneles, preview y widgets reutilizables de PySide6.
- `main.py`: launcher de la app desktop.

Ejecutar desde la raiz del repo:

```powershell
python -m desktop.main
```

Opciones:

```powershell
python -m desktop.main --hide-overlay
python -m desktop.main --hide-floating
python -m desktop.main --enable-perception-tools
```

El desktop consume `rtda.complement.RTDAComplementRuntime`; no debe contener
logica core de captura, acciones, vision ni MCP.
