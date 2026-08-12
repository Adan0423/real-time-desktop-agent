# 🚀 Guía de Instalación y Distribución — Real-Time Desktop Agent (RTDA)

> **Versión**: 0.1.0 | **Plataforma**: Windows 11 | **Protocolo**: Model Context Protocol (MCP)

---

## ❓ 1. ¿Cómo funciona la compilación y empaquetado?

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           SRC / RTDA MODULE                             │
│                  Código fuente Python interpretado                      │
│     (src/rtda/capture, perception, actions, agent, session, mcp)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
                      .\scripts\build_mcpb.ps1
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIST ARCHIVE (.mcpb Bundle)                          │
│          dist/real-time-desktop-agent-0.1.0.mcpb (243 KB)             │
│   Contiene todo el runtime, manifest.json y dependencias empaquetadas   │
└─────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> **El código fuente Python no se compila a un archivo ejecutable `.exe` binario.**
> En su lugar, el script `build_mcpb.ps1` empaqueta el módulo `rtda` junto con su `manifest.json` en un archivo comprimido estándar `.mcpb` (MCP Bundle) de **1 Click** compatible con Claude Desktop y otros clientes MCP.

---

## 🛠️ 2. Métodos de Instalación para Diferentes Plataformas

Elige el método según el cliente de IA que desees conectar:

```text
                                  INSTALACIÓN
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
   MÉTODO A: CLAUDE             MÉTODO B: DEVELOPER           MÉTODO C: NETWORK / API
   Instalación 1-Click          pip / uv local install        ChatGPT / WebSocket / SSE
   (Archivo .mcpb)              (Cursor, VSCode, Windsurf)    (Servidor en Red)
```

---

### 🟣 Método A: Claude Desktop (Instalación 1-Click con archivo `.mcpb`)

Este es el método **más rápido y recomendado** para usuarios finales de Claude Desktop.

> [!TIP]
> No requiere tener Python previamente instalado ni clonar el código fuente.

#### Pasos:
1. **Obtener el archivo `.mcpb`**:
   Descarga el paquete distribuible desde:
   `dist/real-time-desktop-agent-0.1.0.mcpb`

2. **Instalar en Claude Desktop**:
   - Abre **Claude Desktop**.
   - Ve a **Settings** ⚙️ ➔ **Developer** ➔ **Add Extension**.
   - Selecciona el archivo `real-time-desktop-agent-0.1.0.mcpb` (o simplemente arrástralo sobre la ventana de Claude Desktop).

3. **¡Listo!**:
   Claude Desktop instalará automáticamente las herramientas y podrás pedirle a Claude que interactúe con tu escritorio de Windows.

---

### 🔵 Método B: Desarrolladores / Cursor / VSCode / Windsurf (`pip` / `uv`)

Ideal para desarrolladores que desean modificar el código fuente o conectar clientes localmente via `stdio`.

#### Pasos:
1. **Clonar el repositorio e instalar**:
   ```powershell
   git clone https://github.com/Adan0423/real-time-desktop-agent.git
   cd real-time-desktop-agent

   # Usando uv (Recomendado):
   uv pip install -e .

   # O usando pip tradicional:
   pip install -e .
   ```

2. **Configurar el cliente MCP (`claude_desktop_config.json` o configuración de Cursor/VSCode)**:
   Añade el servidor MCP a la configuración de tu cliente:
   ```json
   {
     "mcpServers": {
       "real-time-desktop-agent": {
         "command": "python",
         "args": ["-m", "rtda.mcp.server", "--transport", "stdio"]
       }
     }
   }
   ```

3. **Verificar instalación**:
   Ejecuta en terminal para comprobar que las herramientas se listan correctamente:
   ```powershell
   python -m rtda.mcp.server --transport stdio
   ```

---

### 🔴 Método C: ChatGPT / Agentes Locales / WebSocket (Servidor SSE en Red)

Ideal para conectar ChatGPT, agentes de voz o servicios que se comunican a través de la red local via HTTP / Server-Sent Events (SSE).

#### Pasos:
1. **Iniciar el servidor MCP en modo SSE**:
   ```powershell
   python -m rtda.mcp.server --transport sse
   ```

2. **Conectar el cliente HTTP / SSE**:
   El servidor escuchará en el puerto local por defecto:
   - **URL SSE**: `http://localhost:8000/sse`
   - **URL de Mensajes**: `http://localhost:8000/messages`

3. **Conectar ChatGPT o Agentes Locales**:
   Configura tu cliente para apuntar al endpoint `http://localhost:8000/sse`.

---

## 🧰 3. Resumen de Herramientas MCP Incluidas

Una vez instalado, el agente expone las siguientes herramientas de tiempo real:

| Herramienta | Descripción | Canal |
|---|---|---|
| 🔍 `observe_state` | Retorna el estado actual de la pantalla (ventana activa, app, lista de elementos UIA) | Data Channel |
| ⚡ `run_task` | Ejecuta un ciclo multi-paso completo (`OBSERVE → PLAN → ACT → VERIFY → RECOVER`) | Control Channel |
| 🖱️ `execute_action` | Ejecuta una acción individual de mouse/teclado (`click`, `type`, `hotkey`, `scroll`, `navigate`) | Win32 SendInput |
| 📑 `desktop_find` | Busca un elemento por texto o tipo en la ventana activa sin solicitar imágenes | Data Channel |
| 🪟 `get_focused_window` | Retorna la ventana que tiene el foco actual en Windows | Data Channel |
| 📊 `session_status` | Muestra el estado y tiempo de actividad de la `DesktopSession` persistente | Status |
| 🩺 `health` | Diagnóstico de salud y fases activas del agente | Diagnostics |

---

## 🧱 4. Requisitos del Sistema

- **Sistema Operativo**: Windows 11 / Windows 10 (Build 19041+)
- **Python**: 3.12, 3.13 o 3.14 (para instalación por código fuente)
- **Permisos**: Permiso de usuario estándar para interacción con la UI de Windows.
