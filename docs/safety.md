# Safety

La seguridad esta activa desde Fase 5:

- `ActionPolicy`: clasifica acciones.
- `ConfirmationManager`: registra confirmaciones explicitas.
- `ActionGuard`: bloquea acciones peligrosas sin confirmacion.

Las herramientas MCP solo exponen `dry_run_action`, no ejecucion real.
