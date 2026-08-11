# Vision

## Fase 6

Se agregan dos piezas:

- `VisionModel`: interfaz abstracta con `analyze` y `locate`.
- `ONNXRuntimeVisionModel`: adaptador fino para cargar modelos locales ONNX cuando exista un modelo.
- `StructuredVisionModel`: implementacion local que razona sobre elementos ya percibidos.

No hay acoplamiento a un proveedor cloud. La fase queda lista para conectar un modelo local o remoto sin cambiar el resto del sistema.
