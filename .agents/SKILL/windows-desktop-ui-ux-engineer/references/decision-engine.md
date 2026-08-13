# Decision Engine

## 1. Clasificar el encargo

Identifica primero si es:

- auditoría UX/UI;
- rediseño localizado;
- rediseño amplio;
- nueva funcionalidad;
- producto desde cero;
- modernización técnica + visual;
- creación de design system;
- corrección de regresión visual;
- implementación desde Figma/mockup;
- optimización de accesibilidad/productividad.

## 2. Elegir estrategia

### DESIGN_FIRST

Úsalo si se cumplen varios de estos factores:

- producto nuevo;
- arquitectura de información indefinida;
- múltiples flujos conectados;
- gran cambio conceptual;
- usuarios/roles diversos;
- alto costo de reescritura;
- necesidad de comparar varias direcciones;
- stakeholders necesitan validar antes de implementación.

Salida mínima antes del código: mapa de tareas, flujo, estructura, dirección visual, componentes críticos y estados.

### CODE_FIRST

Úsalo si:

- el flujo ya está definido;
- el cambio es local o incremental;
- el framework determina mucho del resultado visual;
- ejecutar la aplicación es rápido;
- el feedback visual puede obtenerse en minutos de iteración;
- existe design system reutilizable.

No uses code-first como excusa para ignorar arquitectura UX.

### HYBRID

Úsalo si:

- solo algunas áreas tienen alta incertidumbre;
- un shell/navegación merece diseño previo pero el resto puede iterarse en código;
- hay que formalizar tokens/componentes y después implementarlos;
- el proyecto existente tiene deuda que debe corregirse mientras se rediseña.

## 3. Alcance mínimo efectivo

Antes de tocar archivos, define:

- archivos/componentes directamente afectados;
- componentes compartidos indirectamente afectados;
- pantallas que deben volver a probarse;
- riesgos de regresión;
- posibilidad de rollback.

Evita “rediseñar todo” si el objetivo puede resolverse con una intervención menor.

## 4. Dirección visual

Puntúa mentalmente:

- productividad/densidad;
- necesidad de familiaridad Windows;
- branding;
- creatividad;
- touch vs mouse/keyboard;
- complejidad de datos;
- frecuencia de uso;
- nivel experto del usuario.

La dirección visual debe responder a estos factores, no a tendencias genéricas.
