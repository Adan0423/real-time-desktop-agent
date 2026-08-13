# Visual QA

## Matriz mínima

### Layout
- alineación consistente;
- spacing basado en tokens;
- no clipping;
- no overflow inesperado;
- anchors/grids correctos;
- contenido útil visible sin espacio desperdiciado.

### Windowing
- tamaño inicial razonable;
- tamaño mínimo usable;
- resize intermedio;
- maximizado;
- multi-monitor si es relevante;
- DPI/escalado cuando se pueda probar.

### Tipografía
- jerarquía clara;
- longitud y wrapping correctos;
- truncamiento deliberado con affordance cuando sea necesario;
- escalado de texto razonable.

### Temas
- light;
- dark;
- high contrast si el stack lo permite;
- color semántico preservado.

### Interacción
- hover;
- pressed;
- focus;
- selected;
- disabled;
- drag/drop si aplica;
- context menu;
- tooltips solo donde aporten valor.

### Estados de datos
- loading;
- empty;
- partial;
- error;
- success;
- offline/permission denied cuando aplique.

### Accesibilidad
- focus visible;
- tab order;
- keyboard activation;
- labels;
- contraste;
- no dependencia exclusiva del color.

### Consistencia
- iconos;
- radios;
- alturas de controles;
- padding;
- títulos;
- command placement;
- dialogs.

## Ciclo de corrección

Para cada defecto:

1. reproduce;
2. identifica si es layout, token, componente, tema, datos o framework;
3. corrige la causa raíz, no solo el síntoma;
4. reejecuta;
5. vuelve a inspeccionar la pantalla original;
6. inspecciona consumidores del componente compartido.

## Regresión visual

Si existe infraestructura de snapshots/screenshots, úsala. Si no, realiza comparación estructurada con capturas antes/después cuando sea posible.

No declares pixel-perfect si no existe una referencia visual precisa.
