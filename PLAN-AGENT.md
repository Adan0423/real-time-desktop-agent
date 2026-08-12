# REAL-TIME DESKTOP AGENT — Plan Maestro v2

> **Versión**: 2.0 | **Fecha**: 2026-08-12 | **Estado actual**: Fase 7 en progreso

---

## Objetivo

Construir un agente de escritorio para **Windows 11** capaz de:

1. Observar continuamente la pantalla y el árbol de UI
2. Comprender el estado visual de cualquier aplicación
3. Planificar acciones de múltiples pasos
4. Ejecutar acciones con mouse y teclado
5. Verificar que cada acción tuvo el efecto esperado
6. Recuperarse automáticamente si algo falla
7. Mantener contexto entre pasos sin perder el hilo

**Principio fundamental:** `FAST PERCEPTION + SLOW REASONING`

```text
REAL-TIME SCREEN STREAM
        ↓
FRAME BUFFER (memoria, no disco)
        ↓
CHANGE DETECTION (OpenCV)
        ↓
PERCEPTION PIPELINE (UIA → OCR → OpenCV → Vision AI)
        ↓
UI STATE (representación estructurada)
        ↓
AGENT LOOP: OBSERVE → PLAN → ACT → VERIFY → RECOVER
        ↓
ACCIÓN (mouse, teclado)
        ↓
VERIFICACIÓN VISUAL REAL
        ↓
CONTINUAR O RECUPERAR
```

---

## Arquitectura general

```text
                  REAL-TIME DESKTOP AGENT
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
  CAPTURE ENGINE                         WINDOWS UIA
  (DXGI / WGC)                    (UI Automation Inspector)
         │                                     │
         ▼                                     ▼
   FRAME BUFFER                         UIASnapshot
         │                                     │
         └──────────────┬──────────────────────┘
                        ▼
               PERCEPTION ENGINE
            ┌──────────┼──────────┐
            ▼          ▼          ▼
          OCR        OpenCV    Vision AI
            │          │          │
            └──────────┼──────────┘
                       ▼
                    UI STATE
                       │
                  AGENT OBSERVER
                       │
               ┌───────┴───────┐
               ▼               ▼
           PLANNER          VERIFIER
               │               │
               ▼               ▼
          ACTION PLAN     VERIFICATION
               │               │
          ACTION ENGINE         │
               │               │
         ┌─────┴─────┐         │
         ▼           ▼         │
       MOUSE      KEYBOARD      │
         │           │         │
         └─────┬─────┘         │
               ▼               │
           RESULTADO ──────────┘
               │
           RECOVERY (si falla)
```

---

## Stack tecnológico

| Área | Tecnología | Propósito |
|---|---|---|
| Captura | `windows-capture` (DXGI/WGC) | Stream de frames de baja latencia |
| UI Automation | `uiautomation` | Árbol de elementos de Windows |
| Computer Vision | `opencv-python`, `numpy` | Detección de cambios, template matching |
| OCR | `paddleocr` (opcional) | Lectura de texto en pantalla |
| Vision AI | ONNX Runtime | Modelos locales de visión |
| Acciones | `pyautogui` | Mouse y teclado (reemplazable) |
| IA / Agentes | MCP + FastMCP | Interfaz con Claude Desktop |
| Datos | `pydantic` | Modelos tipados y validados |
| UI App | `PySide6` | Dashboard de escritorio |
| Tests | `pytest` | Suite de pruebas automatizadas |

---

## Fases de desarrollo

### ✅ FASE 1 — Capture Engine

**Objetivo:** Captura estable y de baja latencia.

```text
Monitor / Ventana
      ↓
DXGI / WGC Backend
      ↓
Frame Buffer (en memoria, max 4 frames)
      ↓
FPS + Latencia medidos
```

**Estado:** IMPLEMENTADO · TESTEADO · MEDIDO
- DXGI: ~5ms latencia, 60 FPS estables
- WGC: captura ventanas específicas
- Buffer configurable: `target_fps`, `max_buffer_size`, `region`, `monitor_index`

---

### ✅ FASE 2 — Change Detection

**Objetivo:** Detectar cuándo la UI cambia para no procesar frames idénticos.

```text
Frame anterior + Frame nuevo
        ↓
OpenCV absdiff + umbral
        ↓
ChangeDetectionResult (regions, ratio, latency)
```

**Estado:** IMPLEMENTADO · TESTEADO
- `FrameChangeProcessor` detecta cambios entre pares de frames
- `ProcessingMetrics` registra latencia, FPS, ratio

---

### ✅ FASE 3 — Windows UI Automation

**Objetivo:** Leer el árbol de elementos de UI de Windows.

```text
Ventana activa
      ↓
WindowsUIAutomationInspector
      ↓
UIASnapshot (elements, bbox, name, type, automation_id)
      ↓
PerceptionElement (tipo normalizado para el agente)
```

**Estado:** IMPLEMENTADO · TESTEADO · MEDIDO
- Timeout configurable, límite de profundidad y elementos
- Conversión automática `UIAElement → PerceptionElement`
- Latencia típica: 20-200ms

---

### ✅ FASE 4 — OCR (opcional)

**Objetivo:** Leer texto en pantalla que UIA no puede ver.

```text
Frame → PaddleOCR → (text, bbox, confidence)
```

**Estado:** IMPLEMENTADO como extra opcional (`pip install .[ocr]`)

---

### ✅ FASE 5 — Action Engine

**Objetivo:** Ejecutar acciones de mouse y teclado de forma segura.

```text
ActionCommand (semántico)
      ↓
ActionGuard (safety policy)
      ↓
TargetResolver (text → coordenadas por UIA)
      ↓
PyAutoGUIActionExecutor
      ↓
Mouse / Keyboard (real o dry_run)
```

**Estado:** IMPLEMENTADO · TESTEADO
- `dry_run=True` por defecto (seguro)
- `dry_run=False` para ejecución real (configurable por tool MCP)
- Acciones: click, type, press, hotkey, scroll, navigate, move, hover

---

### ✅ FASE 6 — Safety

**Objetivo:** Clasificar y controlar acciones por nivel de riesgo.

| Nivel | Acciones |
|---|---|
| SAFE | move, hover, scroll, read, inspect |
| MODERATE | click, type, press, hotkey, navigate |
| DANGEROUS | delete, publish, send, purchase, submit |

**Estado:** IMPLEMENTADO · TESTEADO
- `ActionPolicy` + `ActionGuard` + `ConfirmationManager`

---

### 🔄 FASE 7 — Agent Loop (EN PROGRESO)

**Objetivo:** Loop completo `OBSERVE → PLAN → ACT → VERIFY → RECOVER`.

```text
AgentObserver
      ↓
UIState (ventana activa + elementos UIA reales)
      ↓
RuleBasedPlanner (con historial, multi-paso)
      ↓
ActionEngine (dry_run configurable)
      ↓
Verifier (diff UIA real, no timestamp falso)
      ↓
RecoveryManager (estrategias ejecutables)
      ↓
AgentExecutor.run_task() (loop hasta éxito o max_steps)
```

**Estado:** EN PROGRESO — implementado, pendiente benchmark

**Nuevas capacidades (v2):**
- `AgentObserver`: detecta ventana activa con ctypes (sin deps extra)
- `UIState.with_observation()`: actualiza estado desde UIA real
- `UIState.action_history`: memoria de acciones entre pasos
- `run_task(goal, max_steps)`: loop completo multi-paso
- `Verifier`: diff real de elementos UIA (no timestamp falso)
- `RecoveryManager`: estrategias reales (scroll, Escape, INSPECT)
- `RecoveryStep.execute=True`: recovery se ejecuta automáticamente

---

### ⬜ FASE 8 — MCP Server & Complemento

**Objetivo:** Exponer RTDA como complemento para Claude Desktop y otros hosts MCP.

**Estado:** IMPLEMENTADO · FUNCIONAL

**Herramientas MCP disponibles:**

| Tool | Descripción |
|---|---|
| `health` | Estado del servidor |
| `inspect_uia` | Árbol UIA de una ventana |
| `capture_monitors` | Lista de monitores |
| `capture_diagnostic` | Diagnóstico de captura con métricas |
| `plan_goal` | Genera plan desde instrucción |
| `classify_action` | Clasifica riesgo de una acción |
| `dry_run_action` | Simula una acción |
| `get_focused_window` | ⭐ Ventana activa actual |
| `observe_state` | ⭐ Observación completa del escritorio |
| `run_task` | ⭐ Tarea multi-paso con loop completo |
| `execute_action` | ⭐ Acción única con dry_run configurable |

---

## Criterios de evaluación del agente

Un agente de control de escritorio robusto debe poder:

| Criterio | Cómo medirlo |
|---|---|
| Interpretar instrucción | % de instrucciones que generan un plan no vacío |
| Entender estado visual | UIState contiene ventana + elementos reales en cada ciclo |
| Decidir siguiente acción | Tasa de planes correctos sobre instrucciones dadas |
| Usar mouse/teclado | % de acciones SUCCESS vs FAILED en ejecución real |
| Verificar resultado | % de verificaciones con diff real (no fallback) |
| Recuperarse si falla | % de recoveries que desbloquean el ciclo siguiente |
| Tareas largas | Completar tareas de 5+ pasos sin perder contexto |
| Velocidad del ciclo | Latencia end-to-end observe→act < 500ms |
| Detectar cambio de ventana | `focused_window` correcto después de cada acción |
| Telemetría | `elapsed_ms` por fase disponible en cada resultado |

---

## Benchmark de tareas representativas

### Nivel 1 — Acción simple (1 paso)
- Hacer click en un botón específico
- Escribir texto en un campo
- Presionar una tecla de atajo
- Hacer scroll en una ventana

### Nivel 2 — Multi-paso (2-3 pasos)
- Abrir una aplicación y esperar que cargue
- Crear un archivo nuevo y guardarlo con nombre
- Seleccionar texto y copiarlo

### Nivel 3 — Multi-ventana (4-6 pasos)
- Copiar datos de una app a otra
- Navegar entre ventanas y ejecutar acción en cada una
- Completar un formulario con varios campos

### Nivel 4 — Secuencia completa (7+ pasos)
- Abrir app → crear documento → escribir contenido → guardar → cerrar
- Buscar información en una página → copiarla → pegarla en otro lugar
- Ejecutar una secuencia completa de trabajo sin intervención

---

## Reglas de desarrollo

### Nunca hacer
- Construir todo en un único archivo
- Usar screenshots guardados en disco para el loop
- Enviar cada frame a una API de IA
- Usar IA para detectar elementos que UIA puede leer
- Ejecutar acciones destructivas sin validación
- Meter sleeps arbitrarios sin medir
- Ocultar errores
- Ignorar métricas
- Avanzar a la siguiente fase si la anterior no está testeada

### Siempre hacer
- Medir latencia por fase (observe_ms, plan_ms, execute_ms, verify_ms)
- Verificar antes de asumir éxito
- Exponer dry_run antes de ejecutar en producción
- Documentar decisiones de diseño
- Testear cada módulo de forma aislada

---

## Métricas objetivo

```text
Ciclo completo observe→act:   < 500ms
UIA snapshot latencia:        < 200ms
Captura DXGI latencia:        < 10ms
Resolución de target:         < 50ms
Verificación post-acción:     < 400ms (incluye wait_ms)
```

---

## Roadmap de mejoras pendientes

| Prioridad | Mejora |
|---|---|
| 🔴 P1 | Benchmark automatizado de tareas (20-30 pruebas) |
| 🔴 P1 | Telemetría por fase en AgentTaskResult |
| 🟡 P2 | Resolver con UIA live cuando target no está en elementos |
| 🟡 P2 | Integración OCR en pipeline de percepción |
| 🟡 P2 | Detección de diálogos / popups inesperados |
| 🟠 P3 | Vision AI local (ONNX) para elementos no detectables por UIA |
| 🟠 P3 | Memoria persistente entre sesiones del agente |
| 🟠 P3 | Dashboard de métricas en tiempo real |