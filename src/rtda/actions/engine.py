from __future__ import annotations

import time
from dataclasses import dataclass, field

from rtda.actions.interface import ActionExecutor
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.actions.resolver import TargetResolver
from rtda.models.actions import ActionCommand, ActionResult, ActionStatus
from rtda.safety.action_guard import ActionGuard
from rtda.safety.confirmation import ConfirmationManager
from rtda.safety.policy import ActionPolicy


@dataclass(slots=True)
class ActionEngine:
    resolver: TargetResolver = field(default_factory=TargetResolver)
    guard: ActionGuard = field(
        default_factory=lambda: ActionGuard(policy=ActionPolicy(), confirmations=ConfirmationManager())
    )
    executor: ActionExecutor = field(default_factory=PyAutoGUIActionExecutor)

    def execute(self, command: ActionCommand) -> ActionResult:
        started = time.perf_counter()
        allowed, risk, message = self.guard.allowed(command)
        if not allowed:
            return ActionResult(
                command=command,
                status=ActionStatus.BLOCKED,
                risk=risk,
                message=message,
                latency_ms=(time.perf_counter() - started) * 1000.0,
            )
        resolved = self.resolver.resolve(command, risk)
        result = self.executor.execute(resolved)
        result.latency_ms = (time.perf_counter() - started) * 1000.0
        return result
