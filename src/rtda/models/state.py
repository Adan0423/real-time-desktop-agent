from __future__ import annotations

import time
from dataclasses import dataclass, field

from rtda.models.actions import ActionResult
from rtda.models.perception import ChangeDetectionResult, PerceptionElement, UIASnapshot


@dataclass(frozen=True, slots=True)
class UIState:
    application: str | None = None
    window: str | None = None
    focused_window: str | None = None
    page: str | None = None
    elements: tuple[PerceptionElement, ...] = ()
    dialogs: tuple[PerceptionElement, ...] = ()
    notifications: tuple[PerceptionElement, ...] = ()
    last_action: ActionResult | None = None
    action_history: tuple[ActionResult, ...] = ()
    last_change: ChangeDetectionResult | None = None
    uia_snapshot: UIASnapshot | None = None
    timestamp: float = field(default_factory=time.time)

    def find_elements(self, target: str) -> tuple[PerceptionElement, ...]:
        needle = target.casefold()
        return tuple(
            element
            for element in self.elements
            if (element.text and needle in element.text.casefold()) or needle in element.type.casefold()
        )

    def with_action(self, action: ActionResult) -> "UIState":
        history = self.action_history + (action,)
        return UIState(
            application=self.application,
            window=self.window,
            focused_window=self.focused_window,
            page=self.page,
            elements=self.elements,
            dialogs=self.dialogs,
            notifications=self.notifications,
            last_action=action,
            action_history=history,
            last_change=self.last_change,
            uia_snapshot=self.uia_snapshot,
        )

    def with_observation(
        self,
        *,
        focused_window: str | None,
        application: str | None,
        elements: tuple[PerceptionElement, ...],
        uia_snapshot: UIASnapshot | None,
    ) -> "UIState":
        """Return a new UIState updated with a fresh real observation."""
        return UIState(
            application=application or self.application,
            window=focused_window or self.window,
            focused_window=focused_window,
            page=self.page,
            elements=elements,
            dialogs=self.dialogs,
            notifications=self.notifications,
            last_action=self.last_action,
            action_history=self.action_history,
            last_change=self.last_change,
            uia_snapshot=uia_snapshot,
        )

