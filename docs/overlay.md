# Overlay verde

## Objetivo

Cuando RTDA esta capturando, la app propia muestra un marco verde encima del
area observada. Esto ayuda a saber si el motor esta viendo un monitor completo,
una region o una ventana concreta.

La UI lo activa por defecto:

```powershell
python -m rtda.app.main
```

Para ocultarlo:

```powershell
python -m rtda.app.main --hide-overlay
```

## Implementacion

- `rtda.overlay.geometry` calcula el rectangulo de captura.
- `rtda.overlay.windows` resuelve bounds de ventana por titulo.
- `rtda.overlay.qt` dibuja un `QWidget` transparente, topmost y click-through.

Para ventanas se intenta primero `DwmGetWindowAttribute` con
`DWMWA_EXTENDED_FRAME_BOUNDS`, porque representa mejor el marco visible. Si no
esta disponible, se usa `GetWindowRect`.

## Fuentes consultadas

- [GetWindowRect](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowrect)
- [DwmGetWindowAttribute](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/nf-dwmapi-dwmgetwindowattribute)
- [EnumWindows](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows)

## Limitaciones

- El overlay existe en la app propia. En modo MCP, el host externo consume tools
  y no necesariamente abre UI local.
- En captura de ventana, el rectangulo se recalcula periodicamente porque la
  ventana puede moverse.
- Si Windows no permite ubicar una ventana por titulo, el overlay se oculta para
  evitar marcar una zona incorrecta.
