# Implementation Safety

## Antes de modificar

- Identifica build command.
- Identifica tests/lint/typecheck.
- Localiza archivos generados que no deben editarse.
- Localiza convenciones de componentes/estilos.
- Comprueba estado del repositorio si hay VCS disponible.
- Delimita archivos a tocar.

## Guardrails

No:

- borres funcionalidad para simplificar el layout;
- cambies APIs públicas sin necesidad;
- modifiques modelos/persistencia por un cambio visual salvo requisito explícito;
- añadas dependencias grandes sin justificar;
- dupliques un componente existente;
- hardcodees secretos, rutas locales o credenciales;
- desactives validaciones/seguridad para “hacer funcionar” la UI;
- ocultes errores de compilación con casts o flags inseguros sin entender la causa.

## Refactor incremental

Orden preferido:

1. introducir tokens/estilos compartidos;
2. corregir primitives de layout;
3. consolidar componentes duplicados;
4. modernizar navegación/shell si hace falta;
5. migrar pantallas gradualmente;
6. eliminar código obsoleto solo después de confirmar no uso.

## Compatibilidad

Preserva:

- rutas y deep links;
- shortcuts existentes salvo conflicto;
- automatización/UI Automation si existe;
- ids/test selectors usados por tests;
- accesibilidad;
- localización/i18n;
- telemetría necesaria;
- comportamiento offline cuando aplique.

## Validación

Después de cada bloque coherente:

- compila;
- ejecuta tests relevantes;
- abre la pantalla;
- comprueba errores runtime;
- realiza QA visual;
- verifica pantallas compartidas afectadas.
