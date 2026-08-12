# PROMPT MAESTRO — REAL-TIME DESKTOP AGENT

Quiero desarrollar un proyecto de software llamado:

**REAL-TIME DESKTOP AGENT**

El objetivo es construir un agente de escritorio para **Windows 11** capaz de observar continuamente la pantalla, comprender el estado visual de las aplicaciones y ejecutar acciones mediante el mouse y teclado del sistema.

El proyecto debe estar diseñado como un **Computer Use / Desktop Vision Agent de tiempo real**, no como un simple bot basado en screenshots.

---

## 1. OBJETIVO PRINCIPAL

Construir un sistema con esta arquitectura conceptual:

```text
                    REAL-TIME DESKTOP AGENT
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      REAL-TIME SCREEN                    WINDOWS UIA
          CAPTURE                    Windows UI Automation
             │                                 │
             ▼                                 ▼
        FRAME BUFFER                     UI ELEMENTS
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                    PERCEPTION ENGINE
                 ┌──────────┼──────────┐
                 ▼          ▼          ▼
               OCR        OpenCV     Vision AI
                 │          │          │
                 └──────────┼──────────┘
                            ▼
                         UI STATE
                            │
                            ▼
                       AI AGENT
                            │
                       ACTION PLAN
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              MOUSE                 KEYBOARD
                 │                     │
                 └──────────┬──────────┘
                            ▼
                         WINDOWS
```

El principio fundamental debe ser:

**FAST PERCEPTION + SLOW REASONING**

La pantalla debe poder capturarse continuamente y mantenerse en memoria, mientras que la IA solamente debe intervenir cuando sea necesario para interpretar o razonar.

NO quiero una arquitectura basada en:

```text
screenshot
→ enviar screenshot a IA
→ esperar
→ hacer click
→ screenshot
→ enviar screenshot a IA
→ esperar
```

Quiero:

```text
REAL-TIME SCREEN STREAM
        ↓
FRAME BUFFER
        ↓
CHANGE DETECTION
        ↓
UIA / OCR / OPENCV
        ↓
UI STATE
        ↓
IA SOLO CUANDO SEA NECESARIO
        ↓
ACTION
        ↓
VERIFY
        ↓
CONTINUAR
```

---

# 2. REFERENCIAS QUE DEBES ESTUDIAR

Antes de escribir código importante, estudia las siguientes tecnologías y proyectos:

### Microsoft UFO²

Repositorio:

https://github.com/microsoft/UFO

Estudia especialmente:

- arquitectura UFO²
- HostAgent
- AppAgent
- Windows UI Automation
- detección híbrida
- acción híbrida
- máquinas de estados
- percepción
- planificación
- ejecución
- verificación
- MCP

No copies ciegamente su arquitectura.

Extrae las ideas útiles y diseña una arquitectura propia, modular y mantenible.

### Windows Graphics Capture

Documentación oficial:

https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture

Estudia cómo:

- capturar una ventana
- capturar un monitor
- recibir frames continuamente
- mantener baja latencia
- evitar conversiones innecesarias
- utilizar GPU cuando sea posible
- gestionar pérdida de frames
- controlar FPS
- liberar recursos correctamente

### Windows UI Automation

Documentación:

https://learn.microsoft.com/en-us/windows/win32/winauto/ui-automation-specification

Estudia:

- AutomationElement
- ControlType
- Name
- BoundingRectangle
- IsEnabled
- patterns
- árbol de elementos
- eventos UIA
- búsqueda de elementos
- interacción con controles

### OpenCV

https://docs.opencv.org/

Estudia:

- image processing
- template matching
- image comparison
- motion/change detection
- contours
- bounding boxes
- preprocessing para OCR

### PaddleOCR

https://github.com/PaddlePaddle/PaddleOCR

Estudia:

- OCR local
- detección de texto
- bounding boxes
- reconocimiento
- rendimiento
- procesamiento por regiones

### ONNX Runtime

https://onnxruntime.ai/

Estudia cómo ejecutar modelos localmente utilizando CPU/GPU.

### OpenAdapt Desktop

https://github.com/OpenAdaptAI/openadapt-desktop

Estudia:

- captura
- grabación
- reproducción
- evidencia
- recuperación
- verificación

### PyAutoGUI

https://pyautogui.readthedocs.io/

Utilízalo inicialmente para prototipos de mouse y teclado, pero deja una interfaz abstracta para posteriormente poder sustituirlo por APIs nativas de Windows.

---

# 3. STACK INICIAL

Utiliza inicialmente:

- Windows 11
- Python 3.12+
- PySide6 para una interfaz gráfica de debugging/monitorización
- NumPy
- OpenCV
- PaddleOCR
- ONNX Runtime
- Pydantic
- pytest
- logging estructurado
- PyAutoGUI para el primer prototipo de input
- Windows Graphics Capture para captura de pantalla
- Windows UI Automation para percepción estructurada

No introduzcas dependencias innecesarias.

Antes de instalar una librería, explica por qué es necesaria.

---

# 4. ARQUITECTURA DEL PROYECTO

Crea una arquitectura modular:

```text
real-time-desktop-agent/

├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── architecture.md
│   ├── capture.md
│   ├── perception.md
│   ├── uia.md
│   ├── vision.md
│   ├── agent.md
│   ├── actions.md
│   ├── safety.md
│   └── performance.md
│
├── src/
│   │
│   ├── capture/
│   │   ├── interface.py
│   │   ├── windows_capture.py
│   │   ├── frame.py
│   │   ├── frame_buffer.py
│   │   └── region.py
│   │
│   ├── perception/
│   │   ├── interface.py
│   │   ├── change_detector.py
│   │   ├── opencv_detector.py
│   │   ├── ocr.py
│   │   ├── uia.py
│   │   └── vision_model.py
│   │
│   ├── state/
│   │   ├── ui_state.py
│   │   ├── state_store.py
│   │   └── state_machine.py
│   │
│   ├── agent/
│   │   ├── planner.py
│   │   ├── reasoning.py
│   │   ├── executor.py
│   │   └── verifier.py
│   │
│   ├── actions/
│   │   ├── interface.py
│   │   ├── mouse.py
│   │   ├── keyboard.py
│   │   ├── scroll.py
│   │   └── navigation.py
│   │
│   ├── safety/
│   │   ├── policy.py
│   │   ├── confirmation.py
│   │   └── action_guard.py
│   │
│   ├── models/
│   │   ├── perception.py
│   │   ├── actions.py
│   │   └── state.py
│   │
│   ├── mcp/
│   │   └── server.py
│   │
│   └── app/
│       ├── main.py
│       └── dashboard.py
│
├── tests/
│
└── examples/
```

---

# 5. PRINCIPIO FUNDAMENTAL DE CAPTURA

La captura debe funcionar como un **stream continuo**.

No guardes cada frame como PNG/JPEG.

No escribas frames al disco salvo para debugging.

Los frames deben permanecer en memoria.

Crear:

```python
class Frame:
    timestamp: float
    width: int
    height: int
    data: ...
```

y:

```python
class FrameBuffer:
    def push(frame):
        ...

    def latest():
        ...

    def previous():
        ...

    def get_region(...):
        ...
```

El buffer debe poder configurarse:

```text
target_fps
max_buffer_size
region
monitor
window
```

El sistema debe descartar frames antiguos cuando sea necesario.

Para un agente interactivo, normalmente importa más:

**LATEST FRAME**

que procesar todos los frames.

---

# 6. PERFORMANCE

Implementa métricas desde el principio:

```text
capture_fps
capture_latency_ms
processing_fps
ocr_latency_ms
opencv_latency_ms
uia_latency_ms
vision_ai_latency_ms
action_latency_ms
end_to_end_latency_ms
dropped_frames
cpu_usage
gpu_usage
memory_usage
```

Crear un módulo:

```text
performance/
```

que permita medir estas métricas.

La aplicación debe mostrar:

```text
Capture FPS: 60
Processing FPS: 15
Dropped Frames: 2
Capture Latency: 4 ms
Vision Latency: 83 ms
AI Calls: 1
```

No asumir que el sistema es rápido.

MEDIR.

---

# 7. PERCEPTION PIPELINE

Crear una pipeline:

```text
FRAME
 ↓
CHANGE DETECTOR
 ↓
UIA
 ↓
OCR
 ↓
OpenCV
 ↓
¿suficiente información?
       │
    ┌──┴──┐
   YES    NO
    │      │
    │      ▼
    │   VISION AI
    │      │
    └──┬───┘
       ▼
   UI STATE
```

Cada detector debe devolver información estructurada.

Ejemplo:

```json
{
  "type": "button",
  "text": "Guardar",
  "bbox": [720, 480, 810, 520],
  "confidence": 0.97,
  "source": "uia"
}
```

Otro ejemplo:

```json
{
  "type": "text",
  "text": "18392",
  "bbox": [400, 280, 470, 305],
  "confidence": 0.94,
  "source": "ocr"
}
```

---

# 8. FUSIÓN DE PERCEPCIÓN

Nunca depender exclusivamente de una fuente.

Crear un sistema de:

```text
UIA
OCR
OpenCV
Vision AI
```

y fusionar los resultados.

Prioridad inicial:

```text
UIA
↓
OCR
↓
OpenCV
↓
Vision AI
```

Pero permitir que la IA resuelva conflictos.

Ejemplo:

```text
UIA dice:
Editar = X:700 Y:400

OCR dice:
Editar = X:702 Y:401

Vision AI dice:
Editar = X:701 Y:402
```

El sistema debe combinar estas evidencias.

---

# 9. UI STATE

Crear una representación persistente del estado actual.

Ejemplo:

```json
{
  "application": "Chrome",
  "window": "Admin",
  "page": "Product Editor",
  "elements": [],
  "dialogs": [],
  "notifications": [],
  "last_action": null,
  "timestamp": 0
}
```

No volver a analizar toda la interfaz si no cambió.

---

# 10. AGENTE

El agente debe seguir:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
ACT
   ↓
VERIFY
   ↓
UPDATE STATE
   ↓
NEXT ACTION
```

No permitir:

```text
PLAN → ejecutar 50 acciones sin verificar
```

Las acciones importantes deben verificarse.

---

# 11. ACTION ENGINE

La IA no debe controlar directamente coordenadas.

La IA debe generar acciones semánticas:

```json
{
  "action": "click",
  "target": "Guardar"
}
```

o:

```json
{
  "action": "type",
  "target": "URL imagen",
  "value": "https://example.com/image.jpg"
}
```

El Action Engine resuelve el target mediante:

```text
UIA
OCR
OpenCV
Vision
```

y solamente entonces ejecuta:

```text
mouse
keyboard
```

---

# 12. VERIFICATION

Después de cada acción relevante:

```text
ACTION
 ↓
WAIT FOR STATE CHANGE
 ↓
OBSERVE
 ↓
VERIFY EXPECTED RESULT
```

Ejemplo:

```text
click "Guardar"

esperar cambio

buscar:
"Producto actualizado correctamente"

si aparece:
SUCCESS

si no aparece:
RECOVER
```

---

# 13. RECOVERY

El agente debe poder recuperarse de:

- elemento no encontrado
- ventana cerrada
- página cambió
- popup inesperado
- timeout
- OCR incorrecto
- visión ambigua
- click incorrecto
- UI congelada

Nunca asumir que la interfaz permanece igual.

---

# 14. SAFETY

Implementar desde el comienzo.

Acciones clasificadas:

### SAFE

```text
move
scroll
hover
read
screenshot
OCR
inspect
```

### MODERATE

```text
click
type
navigate
```

### DANGEROUS

```text
delete
publish
send
purchase
submit
```

Las acciones peligrosas deben tener mecanismos de confirmación.

Crear:

```python
ActionRisk
ActionPolicy
ActionGuard
ConfirmationManager
```

---

# 15. IA

Crear una interfaz abstracta:

```python
class VisionModel:
    async def analyze(self, frame, instruction):
        ...

    async def locate(self, frame, target):
        ...

class ReasoningModel:
    async def plan(self, state, goal):
        ...
```

No acoplar todo el sistema a un único proveedor.

---

# 16. NO HACER

No:

- construir todo en un único archivo;
- utilizar screenshots guardados constantemente;
- enviar cada frame a una API;
- usar IA para detectar elementos simples;
- depender exclusivamente de coordenadas;
- depender exclusivamente del DOM;
- depender exclusivamente de UIA;
- ejecutar acciones destructivas sin validación;
- meter sleeps arbitrarios por todo el código;
- ocultar errores;
- ignorar métricas;
- añadir dependencias innecesarias.

---

# 17. DESARROLLO POR FASES

NO intentes implementar todo de una vez.

### FASE 1

Construir solamente:

```text
Windows Graphics Capture
        ↓
Frame Buffer
        ↓
FPS monitor
        ↓
Preview
```

Objetivo:

**captura estable y de baja latencia.**

---

### FASE 2

Añadir:

```text
OpenCV
 ↓
change detection
```

---

### FASE 3

Añadir:

```text
Windows UI Automation
```

---

### FASE 4

Añadir:

```text
OCR
```

---

### FASE 5

Añadir:

```text
Mouse
Keyboard
```

---

### FASE 6

Añadir:

```text
Vision AI
```

---

### FASE 7

Añadir:

```text
Agent
Planner
Verifier
Recovery
```

---

### FASE 8

Añadir:

```text
MCP
plugins
tools
```

---

# 18. PRIMER OBJETIVO

NO quiero que empieces construyendo el agente de IA.

Primero crea un prototipo funcional llamado:

**RTDA Capture Engine**

Debe:

1. detectar los monitores disponibles;
2. seleccionar un monitor;
3. iniciar captura continua;
4. mantener frames en memoria;
5. mostrar preview;
6. mostrar FPS;
7. mostrar resolución;
8. medir latencia;
9. detectar frames perdidos;
10. permitir detener/reanudar;
11. permitir seleccionar una región;
12. permitir capturar una ventana específica si Windows lo permite.

Debe existir una interfaz:

```python
class ScreenCapture:
    def start(self):
        ...

    def stop(self):
        ...

    def latest_frame(self):
        ...

    def get_fps(self):
        ...

    def get_latency(self):
        ...
```

---

# 19. DOCUMENTACIÓN

Cada módulo debe tener documentación.

Antes de implementar una parte importante:

1. consultar documentación oficial;
2. identificar API correcta;
3. explicar decisiones;
4. implementar;
5. crear prueba;
6. medir rendimiento;
7. documentar resultado.

No inventes APIs.

Si una API de Windows cambia entre versiones, verificar primero la documentación oficial.

---

# 20. FORMA DE TRABAJAR

Quiero que actúes como:

**Senior Windows Systems Engineer + Computer Vision Engineer + AI Agent Architect.**

No quiero que simplemente generes código.

Quiero que:

- analices arquitectura;
- investigues documentación;
- señales problemas técnicos;
- midas rendimiento;
- propongas alternativas;
- escribas código mantenible;
- hagas tests;
- documentes decisiones;
- mantengas compatibilidad con Windows 11.

Cuando exista más de una solución, compara:

```text
opción
latencia
CPU
GPU
complejidad
estabilidad
mantenibilidad
```

y recomienda una.

---

# 21. REGLA CRÍTICA

Nunca avances automáticamente a la siguiente fase si la anterior no está funcionando.

Cada fase debe terminar con:

```text
IMPLEMENTADO
TESTEADO
MEDIDO
DOCUMENTADO
```

Antes de escribir código de una fase, explícame:

1. qué vamos a construir;
2. qué APIs utilizaremos;
3. por qué;
4. qué alternativas existen;
5. cómo mediremos el resultado;
6. qué archivos modificaremos.

Después implementa.

---

# 22. PRIMERA TAREA

Comienza exclusivamente con:

**FASE 1 — RTDA Capture Engine**

Investiga y compara:

1. Windows Graphics Capture
2. Desktop Duplication API
3. MSS
4. DXGI
5. otras alternativas relevantes para captura de escritorio de baja latencia en Windows 11.

Después crea una tabla comparativa:

```text
Tecnología
FPS
Latencia
CPU
GPU
Captura monitor
Captura ventana
Complejidad
Python support
Estabilidad
Recomendación
```

Después de la comparación, elige la mejor arquitectura para RTDA.

NO implementes todavía OCR, OpenCV, IA, UIA, mouse ni teclado.

Primero quiero conseguir una captura de escritorio de alta velocidad, estable y medible.

El objetivo inicial es:

```text
SCREEN
  ↓
LOW-LATENCY CAPTURE
  ↓
FRAME BUFFER
  ↓
REAL-TIME PREVIEW
  ↓
FPS / LATENCY METRICS
```

Construye el proyecto de forma incremental y profesional.