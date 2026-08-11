# Contribuir

Gracias por ayudar a mejorar Real-Time Desktop Agent.

## Requisitos

- Windows 11 para probar captura real.
- Python `>=3.12,<3.15`.
- Git.

## Preparar Entorno

```powershell
git clone https://github.com/Adan0423/real-time-desktop-agent.git
cd real-time-desktop-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[capture,gui,dev]"
```

Para OCR real:

```powershell
python -m pip install -e ".[ocr]"
```

Nota: PaddleOCR/PaddlePaddle puede requerir una version de Python compatible
distinta a la usada por el entorno principal.

## Ejecutar Pruebas

```powershell
python -m pytest
```

Para validar captura real:

```powershell
python -m rtda.app.main --capture-diagnostic --duration 4 --backend dxgi
```

## Estilo de Trabajo

- Mantener cambios pequenos y enfocados.
- No introducir dependencias sin justificar su uso.
- Documentar decisiones tecnicas en `docs/ARCHITECTURE.md`.
- Actualizar `docs/PROGRESS.md` y `docs/TODO.md` cuando cambie el estado.
- Agregar pruebas para comportamiento nuevo.

## Seguridad

RTDA interactua con el escritorio local. Por eso:

- MCP debe mantener acciones reales deshabilitadas por defecto.
- Usa `dry_run_action` para integraciones externas.
- Toda accion peligrosa debe pasar por `ActionGuard`.
- No escribas tokens ni secretos en el repositorio.
- No registres `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ni prompts sensibles en logs.

## Convenciones de Commits

Usar mensajes claros, preferiblemente estilo conventional commits:

```text
feat(capture): agregar diagnostico de region
fix(mcp): corregir payload de capture_monitors
docs(readme): actualizar guia de instalacion
test(agent): cubrir recovery por target faltante
```

## Checklist antes de PR

- [ ] `python -m pytest` pasa.
- [ ] Documentacion actualizada.
- [ ] No hay secretos en el diff.
- [ ] El cambio respeta el modo local-first.
- [ ] Las acciones reales no quedan expuestas por MCP.

## Licencia

Al contribuir aceptas que tus cambios se publiquen bajo la licencia MIT del
proyecto.
