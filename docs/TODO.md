# TODO

Ultima actualizacion: 2026-08-11

## Critico para MVP

1. Conectar el ciclo IA con herramientas RTDA.
   - Estado actual: el panel IA consulta el estado vivo disponible, pero no
     ejecuta acciones provenientes del proveedor.
   - Necesario: protocolo de acciones estructuradas, confirmacion por riesgo,
     verificacion posterior y limite de pasos.

2. Probar `.mcpb` en Claude Desktop.
   - Estado actual: manifest validado y paquete local generado en `dist/real-time-desktop-agent-0.1.0.mcpb`.
   - Necesario: arrastrar el paquete en Claude Desktop, confirmar instalacion y probar tools.

3. Probar plugin ChatGPT/Codex.
   - Estado actual: plugin local y marketplace repo creados.
   - Necesario: reiniciar ChatGPT Desktop, instalar desde marketplace local y probar tools.

4. Separar runtime persistente de la app visual.
   - Estado actual: `RTDAComplementRuntime` separa la frontera en codigo, pero vive in-process.
   - Necesario: modo servicio/proceso local que la app y los hosts IA puedan consumir.

5. Endurecer permisos para acciones reales.
   - Estado actual: MCP usa `dry_run_action`.
   - Necesario: confirmacion explicita, allowlist de ventanas y auditoria de acciones.

6. Seleccion visual de region desde la UI.
   - Estado actual: region por inputs numericos.
   - Necesario: selector interactivo tipo recorte y ajuste desde overlay.

7. Guia de conexion MCP por cliente.
   - Estado actual: comando stdio documentado.
   - Necesario: ejemplos para Claude Desktop, Claude Code, ChatGPT/Codex y otros hosts MCP.

## Mejoras Futuras

1. Backend DXGI nativo con dirty/move rects completos.
2. Icono de bandeja Windows junto al control flotante.
3. Streaming de respuestas IA en el dashboard.
4. Tool calling directo desde proveedores IA.
5. Instalador Windows o release portable.
6. GitHub Actions para tests.
7. Benchmarks reproducibles con contenido animado.
8. Persistencia opcional de sesiones y metricas.
9. Icono, firma y assets para el paquete MCPB.
10. Documentacion bilingue espanol/ingles.

## Deuda Tecnica

- Definir politica de versionado y changelog.
- Separar extras de dependencias para MCPB si el paquete crece.
- Revisar compatibilidad de PaddleOCR/PaddlePaddle con Python 3.14.
- Definir protocolo interno entre app visual y runtime persistente.

## Preguntas Abiertas

- El MVP debe permitir acciones reales o solo observacion + dry-run?
- Que proveedores/modelos gratis deben quedar como presets recomendados y con que rate-limit esperado?
- El paquete MCPB debe incluir dependencias completas o usar runtime `uv`?
- El contacto publico sera correo personal, GitHub Issues o ambos?
