from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class DesktopEvent:
    name: str
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WindowChangedEvent(DesktopEvent):
    def __init__(self, previous_window: str | None, new_window: str | None) -> None:
        super().__init__(
            name="window_changed",
            data={"previous_window": previous_window, "new_window": new_window},
        )


@dataclass(frozen=True, slots=True)
class ScreenChangedEvent(DesktopEvent):
    def __init__(self, changed_ratio: float, region_count: int) -> None:
        super().__init__(
            name="screen_changed",
            data={"changed_ratio": changed_ratio, "region_count": region_count},
        )


@dataclass(frozen=True, slots=True)
class ActionExecutedEvent(DesktopEvent):
    def __init__(self, action: str, target: str | None, status: str, latency_ms: float) -> None:
        super().__init__(
            name="action_executed",
            data={"action": action, "target": target, "status": status, "latency_ms": latency_ms},
        )


EventHandler = Callable[[DesktopEvent], None]


class EventBus:
    """Lightweight in-memory publish/subscribe event bus for RTDA desktop events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._global_handlers: list[EventHandler] = []

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event by name (or '*' for all events)."""
        if event_name == "*":
            self._global_handlers.append(handler)
        else:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event."""
        if event_name == "*":
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)
        elif event_name in self._handlers:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)

    def publish(self, event: DesktopEvent) -> None:
        """Publish an event to all subscribers."""
        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception:
                pass

        if event.name in self._handlers:
            for handler in self._handlers[event.name]:
                try:
                    handler(event)
                except Exception:
                    pass
