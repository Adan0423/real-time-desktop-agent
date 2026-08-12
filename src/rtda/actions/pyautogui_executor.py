from __future__ import annotations

import time
from dataclasses import dataclass

from rtda.actions.interface import ActionExecutor
from rtda.models.actions import ActionResult, ActionStatus, ActionType, ResolvedAction


@dataclass(slots=True)
class PyAutoGUIActionExecutor(ActionExecutor):
    """Executes desktop actions via PyAutoGUI.

    Args:
        dry_run: If True (default), no real mouse/keyboard events are sent.
                 Set to False to execute real actions on the desktop.
        pause_s: Seconds to pause between PyAutoGUI calls (anti-jitter).
    """

    dry_run: bool = True
    pause_s: float = 0.05

    def __post_init__(self) -> None:
        if self.pause_s < 0:
            raise ValueError("pause_s must be non-negative")

    def execute(self, action: ResolvedAction) -> ActionResult:
        started = time.perf_counter()
        command = action.command
        if self.dry_run:
            return ActionResult(
                command=command,
                status=ActionStatus.DRY_RUN,
                risk=action.risk,
                message="dry-run action accepted",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                resolved_bbox=action.bbox,
                metadata={"x": action.x, "y": action.y, "resolved_by": action.resolved_by},
            )

        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.pause_s
        try:
            self._execute_pyautogui(pyautogui, action)
        except Exception as exc:
            return ActionResult(
                command=command,
                status=ActionStatus.FAILED,
                risk=action.risk,
                message=f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                resolved_bbox=action.bbox,
            )
        return ActionResult(
            command=command,
            status=ActionStatus.SUCCESS,
            risk=action.risk,
            message="action executed",
            latency_ms=(time.perf_counter() - started) * 1000.0,
            resolved_bbox=action.bbox,
            metadata={"x": action.x, "y": action.y, "resolved_by": action.resolved_by},
        )

    def _execute_pyautogui(self, pyautogui, action: ResolvedAction) -> None:  # noqa: ANN001
        command = action.command

        if command.action in (ActionType.MOVE, ActionType.HOVER):
            self._require_point(action)
            pyautogui.moveTo(action.x, action.y)

        elif command.action == ActionType.CLICK:
            self._require_point(action)
            pyautogui.click(action.x, action.y)

        elif command.action == ActionType.TYPE:
            if action.x is not None and action.y is not None:
                pyautogui.click(action.x, action.y)
            # Use typewrite for printable ASCII; write handles unicode too
            pyautogui.write(command.value or "", interval=0.02)

        elif command.action == ActionType.PRESS:
            key = command.value or (command.keys[0] if command.keys else "enter")
            pyautogui.press(key)

        elif command.action == ActionType.HOTKEY:
            if not command.keys:
                raise ValueError("hotkey requires keys")
            pyautogui.hotkey(*command.keys)

        elif command.action == ActionType.SCROLL:
            amount = command.amount or 0
            if action.x is not None and action.y is not None:
                pyautogui.scroll(amount, x=action.x, y=action.y)
            else:
                pyautogui.scroll(amount)

        elif command.action == ActionType.NAVIGATE:
            # Open URL or file with the system default handler
            import subprocess
            target = command.value or command.target or ""
            if target:
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            else:
                raise ValueError("navigate requires a value or target")

        else:
            raise ValueError(f"unsupported pyautogui action: {command.action}")

    @staticmethod
    def _require_point(action: ResolvedAction) -> None:
        if action.x is None or action.y is None:
            raise ValueError("action requires a resolved point")
