# Agent

## Fase 7

El agente implementa el ciclo:

```text
OBSERVE -> UNDERSTAND -> PLAN -> ACT -> VERIFY -> RECOVER
```

En esta fase el planner es deterministico (`RuleBasedPlanner`) y ejecuta como maximo una accion antes de verificar. Esto evita el patron peligroso de planificar muchas acciones sin observar.

Componentes:

- `StateStore`
- `StateMachine`
- `RuleBasedPlanner`
- `ActionEngine`
- `Verifier`
- `RecoveryManager`
