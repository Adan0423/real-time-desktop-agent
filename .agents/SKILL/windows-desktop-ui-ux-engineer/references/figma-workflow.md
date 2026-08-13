# Figma Workflow

## Cuándo usar Figma

Úsalo cuando el valor de explorar antes del código sea mayor que el costo de mantener otra representación del producto.

Buenos casos:

- producto nuevo;
- rediseño de navegación/shell;
- design system;
- múltiples variantes visuales;
- aprobación de stakeholders;
- handoff formal;
- prototipo de flujo complejo.

Evítalo para correcciones pequeñas que se validan mejor en la aplicación real.

## Estructura recomendada

- Foundations / tokens
- Components
- Patterns
- Screens
- Flows / prototype
- QA / references si hacen falta

## Componentes

Usa:

- Auto Layout;
- variables/tokens;
- variants;
- component properties;
- estados interactivos;
- light/dark cuando aplique;
- nomenclatura consistente.

Evita frames duplicados con pequeñas diferencias manuales.

## Handoff

Antes de implementar, define:

- componente origen;
- comportamiento responsive/adaptive;
- estados;
- spacing/tokens;
- iconos;
- texto;
- motion relevante;
- casos empty/error/loading.

## Figma ↔ código

No busques pixel-perfect a costa de comportamiento nativo o accesibilidad. La implementación final debe conservar intención visual, jerarquía y ritmo, respetando primitives del framework.
