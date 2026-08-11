# TODO

Ultima actualizacion: 2026-08-11

## Critico para MVP

1. ❌ Enviar screenshot/frame al proveedor IA.
   - Estado actual: el panel IA envia texto y contexto de metricas.
   - Necesario: codificar ultimo frame como imagen y usar entrada multimodal.

2. 🚧 Probar `.mcpb` en Claude Desktop.
   - Estado actual: manifest validado y paquete local generado en `dist/real-time-desktop-agent-0.1.0.mcpb`.
   - Necesario: arrastrar el paquete en Claude Desktop, confirmar instalacion y probar tools.

3. 🚧 Endurecer permisos para acciones reales.
   - Estado actual: MCP usa `dry_run_action`.
   - Necesario: confirmacion explicita, allowlist de ventanas y auditoria de acciones.

4. ❌ Seleccion visual de region desde la UI.
   - Estado actual: region por inputs numericos.
   - Necesario: selector interactivo tipo recorte.

5. ❌ Guia de conexion MCP por cliente.
   - Estado actual: comando stdio documentado.
   - Necesario: ejemplos para Claude Desktop, Claude Code, ChatGPT/Codex y otros hosts MCP.

## Mejoras Futuras

1. Backend DXGI nativo con dirty/move rects completos.
2. Streaming de respuestas IA en el dashboard.
3. Tool calling directo desde proveedores IA.
4. Instalador Windows o release portable.
5. GitHub Actions para tests.
6. Benchmarks reproducibles con contenido animado.
7. Persistencia opcional de sesiones y metricas.
8. Icono, firma y assets para el paquete MCPB.
9. Documentacion bilingue español/ingles.

## Deuda Tecnica

- Definir politica de versionado y changelog.
- Separar extras de dependencias para MCPB si el paquete crece.
- Revisar compatibilidad de PaddleOCR/PaddlePaddle con Python 3.14.

## Preguntas Abiertas

- ¿El MVP debe permitir acciones reales o solo observacion + dry-run?
- ¿El primer proveedor IA productivo sera OpenAI, Anthropic o ambos?
- ¿El paquete MCPB debe incluir dependencias completas o usar runtime `uv`?
- ¿El contacto publico sera correo personal, GitHub Issues o ambos?
