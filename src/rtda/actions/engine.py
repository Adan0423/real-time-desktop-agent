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
    """Coordinates safety-check → resolve → execute for a single action.

    Args:
        resolver:  Resolves action targets to screen coordinates.
        guard:     Applies safety policy before execution.
        executor:  The low-level action driver (PyAutoGUI by default).
        dry_run:   When True (default), no real mouse/keyboard events are fired.
                   Pass dry_run=False to execute real desktop actions.
    """

    resolver: TargetResolver = field(default_factory=TargetResolver)
    guard: ActionGuard = field(
        default_factory=lambda: ActionGuard(policy=ActionPolicy(), confirmations=ConfirmationManager())
    )
    executor: ActionExecutor | None = None
    dry_run: bool = True

    def __post_init__(self) -> None:
        if self.executor is None:
            self.executor = PyAutoGUIActionExecutor(dry_run=self.dry_run)

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
        assert self.executor is not None
        result = self.executor.execute(resolved)
        result.latency_ms = (time.perf_counter() - started) * 1000.0
        return result

