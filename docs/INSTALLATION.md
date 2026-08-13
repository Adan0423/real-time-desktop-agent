# 🚀 Guía de Instalación y Distribución — Real-Time Desktop Agent (RTDA)

> **Versión**: 3.0.1-beta | **Plataforma**: Windows 11 | **Protocolo**: Model Context Protocol (MCP)

---

## 🛠️ 1. Resumen de Métodos de Instalación

Elige el método según el cliente o entorno desde el que te conectarás a RTDA:

```text
                                  INSTALACIÓN RTDA
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
   MÉTODO A: CLAUDE              MÉTODO B: CLIENTES JSON         MÉTODO C: SERVIDOR SSE
   Instalación 1-Click           Cursor, VSCode, Windsurf,       ChatGPT, Agentes Web,
   (Archivo .mcpb)               Roo Code (pip / uvx / venv)     Red Local (HTTP / SSE)
```

---

### 🟣 Método A: Claude Desktop (Instalación 1-Click con archivo `.mcpb`)

Este es el método **más rápido y recomendado** para usuarios de Claude Desktop (no requiere configurar JSON ni usar terminal).

#### Pasos:
1. **Obtener el paquete `.mcpb`**:
   Descarga `real-time-desktop-agent-3.0.1-beta.mcpb` desde las Releases de GitHub o compílalo ejecutando:
   ```powershell
   .\scripts\build_mcpb.ps1
   ```

2. **Instalar en Claude Desktop**:
   - Abre **Claude Desktop**.
   - Ve a **Settings (⚙️) ➔ Developer ➔ Add Extension**.
   - Selecciona el archivo `real-time-desktop-agent-3.0.1-beta.mcpb` (o simplemente **arrástralo y suéltalo dentro de la ventana de Claude Desktop**).

3. **¡Listo!**: Claude reconocerá las herramientas de control de escritorio de forma inmediata.

---

### 🔵 Método B: Clientes con Configuración JSON (Cursor, VSCode, Roo Code, Windsurf)

Para cualquier cliente MCP basado en la configuración estándar JSON (`mcpServers`).

#### 📌 Opción 1: Instalación previa con `pip` (Modo Global Recomendado)

1. **Instalar el paquete en tu Python local:**
   ```powershell
   pip install https://github.com/Adan0423/real-time-desktop-agent/releases/download/v3.0.1-beta/real_time_desktop_agent-3.0.1b0-py3-none-any.whl
   ```

2. **Agregar esta configuración al archivo JSON del cliente MCP:**
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

Si tu cliente soporta `uvx`, no necesitas instalar previamente el paquete. `uvx` descargará e iniciará RTDA a demanda:

```json
{
  "mcpServers": {
    "real-time-desktop-agent": {
      "command": "uvx",
      "args": [
        "--from",
        "https://github.com/Adan0423/real-time-desktop-agent/releases/download/v3.0.1-beta/real_time_desktop_agent-3.0.1b0-py3-none-any.whl",
        "rtda-mcp",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

---

#### 📂 Opción 3: Repositorio clonado localmente

1. **Clonar e instalar dependencias:**
   ```powershell
   git clone https://github.com/Adan0423/real-time-desktop-agent.git
   cd real-time-desktop-agent
   uv pip install -e ".[capture,gui,dev,service]"
   ```

2. **Agregar el JSON apuntando al entorno virtual local:**
   > *Nota: Reemplaza `C:\Path\To\real-time-desktop-agent` por la ruta donde clonaste el proyecto.*

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

---

### 🔴 Método C: ChatGPT / Agentes Locales / WebSocket (Servidor SSE en Red)

Ideal para conectar ChatGPT u otros agentes mediante HTTP / Server-Sent Events (SSE).

1. **Iniciar el servidor MCP en modo SSE:**
   ```powershell
   python -m rtda.mcp.server --transport sse
   ```

2. **Conectar el cliente HTTP / SSE:**
   - **Endpoint SSE**: `http://localhost:8000/sse`
   - **Endpoint de Mensajes**: `http://localhost:8000/messages`

---

## 🖥️ 2. Ejecutar la App de Escritorio Standalone (GUI)

Para abrir la interfaz gráfica nativa con vista previa en tiempo real, marco verde overlay y panel flotante:

```powershell
python -m desktop.main
```

---

## 🧱 3. Requisitos del Sistema

- **Sistema Operativo**: Windows 11 / Windows 10 (Build 19041+)
- **Python**: 3.12, 3.13 o 3.14
- **Permisos**: Permiso de usuario estándar para interacción con la UI de Windows.
