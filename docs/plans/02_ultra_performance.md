# ⚡ Ultra-Performance & Hybrid Architecture

> [!IMPORTANT]
> **Axioma de Rendimiento**: La mayor ganancia de velocidad proviene de **eliminar trabajo innecesario (Work Elimination)** y **evitar copias de memoria (Zero-Copy)**, no solo de optimizar formatos de texto.

---

## 🏎️ 1. Eliminación de Trabajo ("Work Elimination")

En lugar de procesar la pantalla completa 60 veces por segundo:

```text
                       60 FPS Screen Capture (DXGI / WGC)
                                       │
                                       ▼
                         GPU Change Detection (<5ms)
                                       │
                         ┌─────────────┴─────────────┐
                        NO                           SÍ
                         │                           ▼
                   (Skip Frame)             Changed Region (ROI)
                                                     │
                                                     ▼
                                          Tracking + WinEvent
                                                     │
                                                     ▼
                                            OCR / CV solo en ROI
                                                     │
                                                     ▼
                                           ¿Existe Ambigüedad?
                                           ┌─────────┴─────────┐
                                          NO                   SÍ
                                           │                   ▼
                                           ▼              Vision AI (On Demand)
                                    Ejecutar Acción
```

> [!TIP]
> Si de 60 frames capturados solo 4 sufren cambios de UI, el **Work Elimination** descarta el 93% del trabajo de percepción antes de gastar recursos de CPU/GPU.

---

## 🏛️ 2. Arquitectura Híbrida: C++ Core + Python AI Layer

```text
┌────────────────────────────────────────────────────────┐
│                   AI / AGENT LAYER                     │
│                Python 3.12+ / MCP Server               │
│          Planner · Skills · Reasoning · Agent Loop     │
└───────────────────────────┬────────────────────────────┘
                            │
              MCP / gRPC / Protobuf / Shared Memory
                            │
┌───────────────────────────▼────────────────────────────┐
│                    RTDA CORE (C++)                     │
│                                                        │
│  ├── Capture Engine   (WGC / DXGI Duplication D3D11)   │
│  ├── Input Engine     (Win32 Native SendInput <10ms)   │
│  ├── Event Engine     (WinEvents / SetWinEventHook)    │
│  ├── Perception Engine(ROI Change Detection / OpenCV)  │
│  └── Shared Memory    (Zero-Copy Buffer)               │
└────────────────────────────────────────────────────────┘
```

---

## 📊 3. Selección de Formatos por Canal

| Uso / Canal | Formato | Ventaja Principal |
|---|---|---|
| **Frames entre Procesos** | `D3D11 Textures` / `Shared Memory` | Zero-copy en GPU/VRAM. Elimina Base64/PNG. |
| **Eventos de Alta Frecuencia (IPC)** | `Protobuf` / `MessagePack` | Transportes binarios ultra-rápidos (<1ms). |
| **IA ↔ Herramientas (MCP)** | `JSON` / `TOON` | Optimización de tokens para el modelo LLM. |
| **Configuración / Logs** | `JSON` | Formato legible y estándar. |

---

## 🔝 4. Jerarquía de Optimización

1. 🔴 **Event-Driven Architecture**: Reaccionar a eventos nativos Win32 (`SetWinEventHook`) sin polling.
2. 🔴 **Zero-Copy GPU & Shared Memory**: Transferencia de frames sin copias en memoria.
3. 🟡 **Work Elimination (ROI)**: Acotar OCR/CV a las regiones modificadas.
4. 🟡 **C++ Core para Hot Path**: Win32 SendInput, DirectX 11 y captura nativa.
5. 🟠 **Modelos Locales Pequeños (ONNX / DirectML)**: Percepción en pantalla rápida.
6. 🟢 **LLM / VLM Grande**: Exclusivo para razonamiento y planificación de tareas.
