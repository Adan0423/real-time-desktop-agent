from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Any

from rtda.actions.engine import ActionEngine
from rtda.actions.win32_input import Win32SendInputBackend
from rtda.agent.executor import AgentExecutor, AgentTaskResult
from rtda.agent.observer import AgentObserver
from rtda.events.bus import ActionExecutedEvent, EventBus, WindowChangedEvent
from rtda.models.actions import ActionCommand, ActionResult, ActionType
from rtda.models.state import UIState
from rtda.state.state_store import StateStore


@dataclass
class DesktopSession:
    """Represents an always-on persistent session between an AI model and the Windows Desktop.

    Maintains background observation, input controllers, state store, and event bus
    alive across multiple tasks and queries without re-initializing drivers.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connected_ai: str = "Claude Desktop"
    is_active: bool = False

    observer: AgentObserver = field(default_factory=AgentObserver)
    event_bus: EventBus = field(default_factory=EventBus)
    state_store: StateStore = field(default_factory=StateStore)

    use_win32_input: bool = True
    dry_run_by_default: bool = True

    _executor: AgentExecutor | None = field(default=None, init=False)
    _last_window: str | None = field(default=None, init=False)
    _start_time: float = field(default_factory=time.time, init=False)

    def __post_init__(self) -> None:
        backend = (
            Win32SendInputBackend(dry_run=self.dry_run_by_default)
            if self.use_win32_input
            else None
        )
        engine = ActionEngine(executor=backend, dry_run=self.dry_run_by_default)
        self._executor = AgentExecutor(
            state_store=self.state_store,
            observer=self.observer,
            action_engine=engine,
        )

    def start(self) -> None:
        """Start the desktop session."""
        self.is_active = True
        self._start_time = time.time()
        # Take initial observation
        initial_state = self.observer.observe()
        self.state_store.set(initial_state)
        self._last_window = initial_state.focused_window

    def stop(self) -> None:
        """Stop the desktop session."""
        self.is_active = False

    def observe(self, window_title: str | None = None) -> UIState:
        """Observe the desktop state and emit events if window focus changed."""
        state = self.observer.observe(window_title=window_title)
        self.state_store.set(state)

        # Notify EventBus if foreground window changed
        if state.focused_window != self._last_window:
            self.event_bus.publish(
                WindowChangedEvent(previous_window=self._last_window, new_window=state.focused_window)
            )
            self._last_window = state.focused_window

        return state

    def run_task(
        self,
        goal: str,
        *,
        max_steps: int = 10,
        expected_text: str | None = None,
        dry_run: bool | None = None,
    ) -> AgentTaskResult:
        """Run a multi-step task within the active session."""
        if not self.is_active:
            self.start()

        if dry_run is not None and self._executor is not None:
            self._executor.action_engine.dry_run = dry_run
            if isinstance(self._executor.action_engine.executor, Win32SendInputBackend):
                self._executor.action_engine.executor.dry_run = dry_run

        assert self._executor is not None
        result = self._executor.run_task(
            goal,
            max_steps=max_steps,
            expected_text=expected_text,
        )

        # Emit action executed events
        for cycle in result.cycles:
            if cycle.action_results:
                act = cycle.action_results[0]
                self.event_bus.publish(
                    ActionExecutedEvent(
                        action=act.command.action.value,
                        target=act.command.target,
                        status=act.status.value,
                        latency_ms=act.latency_ms,
                    )
                )

        return result

    def execute_action(
        self,
        action: str | ActionType,
        target: str | None = None,
        value: str | None = None,
        keys: list[str] | None = None,
        dry_run: bool | None = None,
    ) -> ActionResult:
        """Execute a single action directly within the session."""
        if not self.is_active:
            self.start()

        effective_dry_run = self.dry_run_by_default if dry_run is None else dry_run
        assert self._executor is not None

        self._executor.action_engine.dry_run = effective_dry_run
        if isinstance(self._executor.action_engine.executor, Win32SendInputBackend):
            self._executor.action_engine.executor.dry_run = effective_dry_run

        command = ActionCommand(
            action=ActionType(action) if isinstance(action, str) else action,
            target=target,
            value=value,
            keys=keys or [],
        )

        result = self._executor.action_engine.execute(command)

        self.event_bus.publish(
            ActionExecutedEvent(
                action=command.action.value,
                target=command.target,
                status=result.status.value,
                latency_ms=result.latency_ms,
            )
        )

        return result

    def get_summary(self) -> dict[str, Any]:
        """Return JSON summary of the active session."""
        current = self.state_store.get()
        return {
            "session_id": self.session_id,
            "connected_ai": self.connected_ai,
            "is_active": self.is_active,
            "uptime_seconds": round(time.time() - self._start_time, 1) if self.is_active else 0.0,
            "focused_window": current.focused_window,
            "application": current.application,
            "element_count": len(current.elements),
            "use_win32_input": self.use_win32_input,
            "dry_run_by_default": self.dry_run_by_default,
        }
