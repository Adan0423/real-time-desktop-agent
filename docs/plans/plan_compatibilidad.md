Lo principal que debes mejorar es la compatibilidad de plataforma y empaquetado. El conector ya inicia y expone 13 herramientas, pero su observación real de pantalla depende de Windows/COM/UI Automation; al ejecutarlo en Linux, observe_state solo devuelve el error de plataforma.
Prioridad
Mejora
Motivo y acción concreta
Alta
Ejecutar RTDA en Windows 10/11
UIA, COM, DXGI/WGC y Win32 SendInput son las bases de la observación/control reales. Instálalo y arráncalo en el equipo Windows que deseas controlar.
Alta
Fijar MCP a <2
El código usa mcp.server.fastmcp, pero la instalación resolvió MCP 2.0.0 y falló. Declara y bloquea explícitamente mcp>=1.27,<2 también en el wheel y el archivo de bloqueo.
Alta
Corregir metadatos del wheel
El pyproject.toml exige MCP <2, pero el wheel publicado permitió <3. Reconstruye y publica el wheel para que ambos coincidan.
Alta
Usar un entorno virtual dedicado
Configura el conector con la ruta al Python de .venv de RTDA, no con python genérico. Así evitas que el cliente use un intérprete sin el módulo o con dependencias incompatibles.
Media
Añadir detección de sistema operativo
Antes de iniciar DesktopSession, detecta Linux/macOS y devuelve un diagnóstico explícito, en vez de iniciar una sesión que luego falla al consultar COM.
Media
Separar herramientas portables de Windows
health, plan_goal, classify_action y el modo seco pueden funcionar en varios sistemas. Registra o habilita las herramientas de captura/UIA solo cuando el backend Windows esté disponible.
Media
Unificar documentación y versión
La guía muestra versión 0.1.0, mientras el paquete/release es 3.0.0b1. Actualiza versión, tag, comandos y matriz de compatibilidad.
Media
Incluir una prueba de arranque automatizada
Agrega una prueba que verifique: importación, health, listado de herramientas MCP y detección del backend Windows. Esto habría detectado el conflicto de MCP antes de publicar.
Para una prueba real de escritorio, el siguiente paso es instalarlo en Windows con Python 3.12–3.14 y ejecutar python -m rtda.mcp.server --transport stdio. Después prueba health, session_status y observe_state; deja dry_run: true hasta confirmar que los datos de ventana y controles son correctos.
Si quieres, puedo ayudarte a preparar un parche concreto para pyproject.toml, el control de plataforma y una prueba de compatibilidad.
