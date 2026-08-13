# 📚 Índice de Planes de Arquitectura y Roadmap Técnico (RTDA)

Este directorio contiene la evolución del diseño de arquitectura, principios de rendimiento y roadmap técnico para el **Real-Time Desktop Agent (RTDA)**.

---

## 📄 Planes y Documentos Disponibles

| Documento | Título | Enfoque Principal | Estado |
|---|---|---|---|
| 🌟 [**`00_master_plan.md`**](00_master_plan.md) | **Plan Maestro Unificado v3.0** | Visión unificada de arquitectura, stack, fases 1-8, reglas de desarrollo y estado técnico global | 🌟 Documento Maestro (Activo) |
| 🛠️ [**`01_runtime_architecture.md`**](01_runtime_architecture.md) | **Desktop Agent Runtime Architecture** | Arquitectura de Capas de Capacidades, `DesktopSession` persistente, `InputService` nativo y canales Data/Visual | ✅ Implementado |
| ⚡ [**`02_ultra_performance.md`**](02_ultra_performance.md) | **Ultra-Performance & Hybrid Architecture** | Eliminación de Trabajo (*Work Elimination* ROI), Memoria Compartida Zero-Copy, Core C++ y Jerarquía de Optimizaciones | ✅ Implementado |
| 📦 [**`03_compatibility_packaging.md`**](03_compatibility_packaging.md) | **Compatibilidad, Empaquetado y Entorno** | Soporte de plataforma Windows vs Linux/macOS, pinning de MCP `<2`, metadatos de wheel y aislamiento en `.venv` | ✅ Implementado |

---

## ⚡ Resumen del Principio Arquitectónico

```text
  SEE CONTINUOUSLY  ──►  ACT IMMEDIATELY  ──►  REASON ONLY WHEN NECESSARY
```

```text
FAST PERCEPTION + SLOW REASONING
```
