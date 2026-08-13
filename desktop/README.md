# 🖥️ RTDA Desktop Control Surface

![Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078D4?logo=windows&logoColor=white)
![UI Framework](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-green?logo=qt)
![Theme](https://img.shields.io/badge/theme-Windows%2011%20Mica-violet)
![RAM Buffer](https://img.shields.io/badge/buffer-Zero--Copy%20RAM-blue)

> **RTDA Desktop Control Surface** es la aplicación de interfaz gráfica independiente para probar, monitorear y controlar en tiempo real el complemento de runtime [`src/rtda/`](../src/rtda/).

---

## 🌟 Características Principales

- 🎨 **Interfaz Moderna Windows 11**: Integración nativa con esquinas redondeadas, tema oscuro y efectos de transparencia **Mica** vía Win32 APIs.
- 📷 **Previsualización de Captura DXGI / WGC**: Transmisión fluida de 60 FPS sin guardado en disco (100% en memoria RAM).
- 🧠 **Integración Multi-Proveedor de IA**: Conexión directa con OpenAI, Anthropic, OpenRouter, Groq, TokenRouter, NVIDIA y servidores locales (Ollama/vLLM) con resolución dinámicas desde `.env`.
- 🔍 **Inspección Visual ROI & UIA**: Visualización en tiempo real de cajas delimitadoras (Bounding Boxes), árboles UIA y detección de cambios por visión computacional.
- 🗔 **Widget Flotante Always-on-Top**: Control compacto en segundo plano con telemetría en vivo (`FPS`, latencia `ms`, frames descartados).
- 🌐 **Modo Dashboard Web**: Servidor web FastAPI/Uvicorn alternativo lanzable desde la misma consola.

---

## 🏗️ Estructura del Módulo `desktop/`

| Componente | Archivo / Carpeta | Descripción |
|---|---|---|
| 🖼️ **Icono de App** | [`assets/icon.png`](assets/icon.png) | Icono vectorial de alta resolución para ventanas y barra de tareas de Windows. |
| 🚀 **Lanzador** | [`main.py`](main.py) | Punto de entrada principal CLI y arranque de la app PySide6/Qt o servidor Web. |
| 🖥️ **Ventana Principal** | [`dashboard.py`](dashboard.py) | Dashboard central PySide6 con preview de frames, sidebar y barra de acciones. |
| 🧠 **Cliente de IA** | [`ai/`](ai/) | Arquitectura modular desacoplada (*Strategy Pattern*) para proveedores OpenAI/Anthropic/Compatibles. |
| 🔌 **Puentes de Runtime** | [`runtime_bridge.py`](runtime_bridge.py) / [`ai_bridge.py`](ai_bridge.py) | Adaptadores asíncronos para conectar la interfaz Qt con el motor de captura y la IA. |
| 🗔 **Control Flotante** | [`floating.py`](floating.py) | Widget transparente siempre visible en primer plano con telemetría. |
| 🎨 **Sistema de Estilos** | [`theme.py`](theme.py) / [`native/`](native/) | Stylesheets HSL/Dark y llamadas Win32 nativas para bordes y efectos Mica. |
| 📐 **Superposición ROI** | [`overlay/`](overlay/) | Ventana transparente de marcación visual sobre la pantalla objetivo. |
| 📦 **Componentes UI** | [`ui/`](ui/) | Paneles modulares: Captura, Métricas, MCP, IA y Configuración. |

---

## ⚡ Comandos de Inicio

Ejecutar desde la raíz del repositorio:

### 1. Iniciar la aplicación GUI de escritorio
```powershell
python -m desktop.main
```

### 2. Habilitar herramientas de percepción (OpenCV, UIA, ROI)
```powershell
python -m desktop.main --enable-perception-tools
```

### 3. Opciones de personalización
```powershell
# Ocultar la ventana flotante en segundo plano
python -m desktop.main --hide-floating

# Ocultar el marco verde de región de captura
python -m desktop.main --hide-overlay

# Fijar buffer de memoria a 1 frame (baja latencia)
python -m desktop.main --max-buffer-size 1

# Iniciar Dashboard Web en el navegador
python -m desktop.main --web
```

---

## ⌨️ Atajos de Teclado (Shortcuts)

| Atajo | Función |
|---|---|
| <kbd>F5</kbd> | 🟢 Iniciar motor de captura |
| <kbd>Shift</kbd> + <kbd>F5</kbd> | 🔴 Detener motor de captura |
| <kbd>Ctrl</kbd> + <kbd>1</kbd> | 📷 Ir a pestaña **Captura** |
| <kbd>Ctrl</kbd> + <kbd>2</kbd> | 📊 Ir a pestaña **Métricas** |
| <kbd>Ctrl</kbd> + <kbd>3</kbd> | 🔌 Ir a pestaña **MCP** |
| <kbd>Ctrl</kbd> + <kbd>4</kbd> | 🧠 Ir a pestaña **IA** |
| <kbd>Ctrl</kbd> + <kbd>5</kbd> | ⚙️ Ir a pestaña **Configuración** |

---

## 🔒 Privacidad y Rendimiento de RAM

> [!NOTE]
> **RTDA Desktop no guarda ningún frame en disco**.
> Toda la transmisión visual habita únicamente en buffers de memoria RAM efímeros (`SharedMemoryFrameBuffer`) y se destruye automáticamente al detener la sesión o cerrar la aplicación.
