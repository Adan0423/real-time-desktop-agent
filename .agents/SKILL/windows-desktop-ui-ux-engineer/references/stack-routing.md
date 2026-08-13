# Stack Routing

## Regla común

Primero detecta el stack real. Después diseña dentro de sus fortalezas. No simules patrones web dentro de frameworks nativos si existen controles adecuados, ni fuerces patrones nativos donde una shell web tiene mejores primitives.

## WinUI 3 / Windows App SDK

- Aprovecha controles Fluent y recursos de tema.
- Prefiere NavigationView/TitleBar/AppWindow y primitives modernos cuando encajen.
- Usa recursos y estilos para tokens; evita hardcode repetido.
- Trata Mica/Acrylic como materiales contextuales.
- Comprueba DPI, windowing, keyboard, light/dark y high contrast.

## WPF

- Respeta MVVM si ya existe.
- Centraliza estilos, ResourceDictionary y DynamicResource donde corresponda.
- Evita mezclar lógica de negocio en code-behind si el proyecto ya usa binding/commands.
- Moderniza de forma incremental; Windows App SDK interop puede ser útil si el caso lo justifica.

## WinForms

- Evita reescritura completa solo por apariencia.
- Mejora layout, spacing, tipografía, escalado DPI y consistencia de controles.
- Considera custom controls con prudencia; no conviertas cada control en renderizado manual.
- Mantén productividad y estabilidad de aplicaciones LOB.

## .NET MAUI

- Distingue necesidades Windows de las compartidas con otras plataformas.
- No rompas layouts móviles para “optimizar Windows”.
- Usa recursos/estilos y adaptaciones por plataforma cuando sean justificadas.

## Electron / React / TypeScript

- Mantén separación entre renderer/main/preload y límites de seguridad.
- Prefiere componentes reutilizables y tokens CSS/variables.
- Cuida bundle, render y listas grandes.
- Integra comportamiento de ventana y shortcuts coherentes con desktop.
- No diseñes como una web metida en una ventana: contempla menús, window chrome, drag regions, keyboard y contexto de escritorio.

## Tauri

- Mantén frontend ligero y respeta el boundary con comandos Rust.
- No añadas dependencias web pesadas sin necesidad.
- Considera capacidades/permissions y surface de seguridad al tocar integraciones del shell.

## Flutter Desktop

- Usa Theme/ColorScheme y widgets adaptativos cuando aporten valor.
- Diseña keyboard/focus explícitamente.
- Evita layouts exclusivamente mobile estirados a escritorio.
- Usa shortcuts/actions y scrolling apropiado para mouse/trackpad.

## Qt / QML

- Reutiliza componentes y tokens QML.
- Evita lógica excesiva dentro de QML si debe vivir en C++/modelo.
- Considera high-DPI, focus, keyboard y native dialogs/windowing cuando corresponda.

## C++ / Win32

- Preserva comportamiento del shell y compatibilidad.
- Moderniza selectivamente con APIs actuales o WinUI/Windows App SDK interop cuando sea viable.
- No sacrifiques rendimiento o integración de sistema por una capa visual innecesaria.

## Stack desconocido

1. Lee manifest/dependencies/build files.
2. Localiza entrypoint y ventana principal.
3. Localiza sistema de estilos/temas.
4. Localiza navegación/routing.
5. Localiza librería de componentes.
6. Localiza scripts de build/test.
7. Solo entonces decide patrón de implementación.
