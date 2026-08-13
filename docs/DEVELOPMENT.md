# 💻 Guía de Desarrollo, Pruebas y Benchmark — RTDA

> **Versión**: 3.0.1-beta | **Plataforma**: Windows 11

---

## 🛠️ 1. Configuración del Entorno de Desarrollo

### 1. Clonar el repositorio
```powershell
git clone https://github.com/Adan0423/real-time-desktop-agent.git
cd real-time-desktop-agent
```

### 2. Crear entorno virtual e instalar dependencias
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install uv
uv pip install -e ".[capture,gui,dev,service]"
```

---

## 🧪 2. Suite de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias e integración en `tests/`:

### Ejecutar todas las pruebas unitarias (85 tests):
```powershell
python -m pytest tests/ -v
```

### Ejecutar la Suite de Benchmark Automatizada (25 casos de uso):
```powershell
python -m pytest tests/test_benchmark.py -v
```

---

## 📦 3. Empaquetado y Distribución

### 1. Generar el paquete Bundle `.mcpb` (Para Claude Desktop):
```powershell
.\scripts\build_mcpb.ps1
```
> El paquete resultante se creará en `dist/real-time-desktop-agent-3.0.1-beta.mcpb`.

### 2. Compilar Rueda Python (`.whl`) y Distribución Fuente (`.tar.gz`):
```powershell
uv build
```
> Los paquetes resultantes se generarán en la carpeta `dist/`.

---

## 🔍 4. Diagnósticos de Captura por Consola (CLI)

Para ejecutar pruebas directas de captura desde la terminal sin abrir la interfaz gráfica:

```powershell
# Listar monitores detectados:
python -m rtda.cli.main --list-monitors

# Diagnóstico de captura DXGI a 60 FPS:
python -m rtda.cli.main --capture-diagnostic --duration 5.0
```
