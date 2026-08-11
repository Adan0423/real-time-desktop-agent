# Actions

## Fase 5

La Fase 5 agrega acciones semanticas. La IA o planner no envian coordenadas directamente:

```json
{"action": "click", "target": "Guardar"}
```

El `ActionEngine`:

1. clasifica riesgo;
2. aplica `ActionGuard`;
3. resuelve target contra elementos percibidos;
4. ejecuta con `PyAutoGUIActionExecutor`.

El executor usa `dry_run=True` por defecto para pruebas y MCP.

## Acciones

- Safe: `move`, `hover`, `scroll`, `read`, `inspect`
- Moderate: `click`, `type`, `press`, `hotkey`, `navigate`
- Dangerous: `delete`, `publish`, `send`, `purchase`, `submit`
