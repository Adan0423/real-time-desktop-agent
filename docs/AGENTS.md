# Agentes

Ultima actualizacion: 2026-08-11

## Definicion en RTDA

En este proyecto, un agente es un flujo local que observa estado, interpreta una
meta, propone una accion, la pasa por seguridad, ejecuta o simula, verifica y
recupera si algo falla.

El agente actual es deterministico y deliberadamente pequeno. No ejecuta cadenas
largas de acciones autonomas.

## AgentExecutor

| Campo | Detalle |
| --- | --- |
| Archivo | `src/rtda/agent/executor.py` |
| Proposito | Coordinar `OBSERVE -> UNDERSTAND -> PLAN -> ACT -> VERIFY -> RECOVER` |
| Inputs | `goal: str`, `expected_text: str | None` |
| Outputs | `AgentRunResult` con plan, resultados, verificacion y recovery |
| Herramientas | `StateStore`, `RuleBasedPlanner`, `ActionEngine`, `Verifier`, `RecoveryManager` |
| Disparo | Llamada explicita desde codigo o futuras tools |

## RuleBasedPlanner

| Campo | Detalle |
| --- | --- |
| Archivo | `src/rtda/agent/planner.py` |
| Proposito | Convertir metas simples en `ActionCommand` |
| Inputs | `UIState`, `goal` |
| Outputs | `ActionPlan` |
| Reglas | `click ...`, `type ...`, `inspect`, match por elementos visibles |

Ejemplo:

```python
RuleBasedPlanner().plan(UIState(), "click Guardar")
```

## Verifier

| Campo | Detalle |
| --- | --- |
| Archivo | `src/rtda/agent/verifier.py` |
| Proposito | Confirmar si una accion tuvo resultado aceptable |
| Inputs | estado antes, estado despues, resultado de accion, texto esperado |
| Outputs | `VerificationResult` |

## RecoveryManager

| Campo | Detalle |
| --- | --- |
| Archivo | `src/rtda/agent/recovery.py` |
| Proposito | Proponer siguiente paso cuando falla la verificacion |
| Outputs | `RecoveryStep` |
| Politica actual | Si falta target, inspeccionar UI; si seguridad bloquea, no accionar |

## Tools MCP

| Tool | Proposito | Output |
| --- | --- | --- |
| `health` | Verificar estado del servidor | JSON con nombre, status y fases |
| `capture_monitors` | Listar monitores disponibles | Lista de monitores |
| `capture_diagnostic` | Probar captura local | Checks y metricas |
| `inspect_uia` | Snapshot UIA acotado | Elementos, latencia, errores |
| `plan_goal` | Generar plan deterministico | Acciones sugeridas |
| `classify_action` | Clasificar riesgo | `allowed`, `risk`, `message` |
| `dry_run_action` | Simular accion | Resultado sin ejecutar |

## Limites

- El planner no usa LLM todavia.
- El MCP no ejecuta acciones reales.
- La UI propia tiene panel IA, pero no alimenta aun el agente con vision
  multimodal.
