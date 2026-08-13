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
│          dist/real-time-desktop-agent-3.0.0-beta.mcpb (243 KB)             │
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
   `dist/real-time-desktop-agent-3.0.0-beta.mcpb`

2. **Instalar en Claude Desktop**:
   - Abre **Claude Desktop**.
   - Ve a **Settings** ⚙️ ➔ **Developer** ➔ **Add Extension**.
   - Selecciona el archivo `real-time-desktop-agent-3.0.0-beta.mcpb` (o simplemente arrástralo sobre la ventana de Claude Desktop).

3. **¡Listo!**:
   Claude Desktop instalará automáticamente las herramientas y podrás pedirle a Claude que interactúe con tu escritorio de Windows.

---

### 🔵 Método B: Clientes con Configuración JSON (Cursor, VSCode, Roo Code, Windsurf)

Ideal para conectar aplicaciones que se integran mediante la especificación estándar JSON de `mcpServers`.

#### 📌 Opción 1: Instalación previa con `pip` (Modo Global Recomendado)

1. **Instalar el paquete en tu entorno Python local:**
   ```powershell
   pip install https://github.com/Adan0423/real-time-desktop-agent/releases/download/v3.0.0-beta.1/real_time_desktop_agent-3.0.0b1-py3-none-any.whl
   ```

2. **Agregar la configuración JSON al cliente MCP:**
   ```json
   {
     "mcpServers": {
       "real-time-desktop-agent": {
         "command": "rtda-mcp",
         "args": [
           "--transport",
           "stdio"
         ]
       }
     }
   }
   ```

---

#### 🚀 Opción 2: Auto-instalación con `uvx` (Cero instalación previa)

Si tu cliente soporta `uv` / `uvx`, no necesitas instalar previamente el paquete. `uvx` descargará y ejecutará RTDA de forma temporal e impulsada por demandas:

```json
{
  "mcpServers": {
    "real-time-desktop-agent": {
      "command": "uvx",
      "args": [
        "--from",
        "https://github.com/Adan0423/real-time-desktop-agent/releases/download/v3.0.0-beta.1/real_time_desktop_agent-3.0.0b1-py3-none-any.whl",
        "rtda-mcp",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

---

#### 📂 Opción 3: Repositorio clonado localmente (Código fuente)

1. **Clonar e instalar dependencias:**
   ```powershell
   git clone https://github.com/Adan0423/real-time-desktop-agent.git
   cd real-time-desktop-agent
   uv pip install -e ".[capture,gui,dev,service]"
   ```

2. **Agregar el JSON apuntando a la ruta de tu entorno virtual:**
   > *Nota: Sustituye `C:\Path\To\real-time-desktop-agent` por la ruta real donde clonaste el proyecto en tu sistema.*

   ```json
   {
     "mcpServers": {
       "real-time-desktop-agent": {
         "command": "C:\\Path\\To\\real-time-desktop-agent\\.venv\\Scripts\\python.exe",
         "args": [
           "-m",
           "rtda.mcp.server",
           "--transport",
           "stdio"
         ]
       }
     }
   }
   ```

3. **Verificar instalación**:
   Ejecuta en tu terminal para comprobar que las herramientas se listan correctamente:
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
