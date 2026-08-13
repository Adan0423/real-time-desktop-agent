# UX Audit Checklist

## Producto
- ¿La propuesta de valor se entiende?
- ¿Las tareas principales son obvias?
- ¿La UI refleja prioridades reales del usuario?

## Arquitectura de información
- ¿La navegación agrupa por intención?
- ¿Hay profundidad innecesaria?
- ¿El usuario conserva contexto?

## Jerarquía
- ¿Existe una acción primaria clara?
- ¿Se distinguen acciones peligrosas?
- ¿La densidad es adecuada al tipo de usuario?

## Consistencia
- ¿Los mismos conceptos usan los mismos componentes?
- ¿Los labels y verbos son consistentes?
- ¿Los estados se comportan igual?

## Eficiencia
- ¿Las tareas frecuentes requieren pocos pasos?
- ¿Hay shortcuts/keyboard donde aportan valor?
- ¿Se puede realizar trabajo repetitivo sin fricción?

## Prevención de errores
- ¿Las acciones destructivas son distinguibles?
- ¿Hay confirmación solo cuando el costo de error lo justifica?
- ¿Existe recuperación/undo cuando es posible?

## Feedback
- ¿La UI confirma acciones?
- ¿Las operaciones largas muestran progreso útil?
- ¿Los errores explican qué pasó y qué hacer?

## Accesibilidad
- teclado;
- focus;
- labels;
- contraste;
- escalado;
- color;
- motion.

## Desktop-specific
- resize;
- multi-window si aplica;
- drag/drop;
- menus/context menus;
- title bar;
- system commands;
- shell integrations;
- file picker/dialogs;
- keyboard-first workflows.

## Severidad

Clasifica hallazgos:

- P0: bloquea tarea crítica o produce pérdida/riesgo grave.
- P1: fricción fuerte o accesibilidad crítica.
- P2: inconsistencia o eficiencia moderada.
- P3: pulido visual/cosmético.

No presentes 30 observaciones cosméticas al mismo nivel que 2 problemas de flujo críticos.
