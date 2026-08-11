from __future__ import annotations

import time
from dataclasses import dataclass, field

from rtda.models.actions import ActionResult
from rtda.models.perception import ChangeDetectionResult, PerceptionElement, UIASnapshot


@dataclass(frozen=True, slots=True)
class UIState:
    application: str | None = None
    window: str | None = None
    page: str | None = None
    elements: tuple[PerceptionElement, ...] = ()
    dialogs: tuple[PerceptionElement, ...] = ()
    notifications: tuple[PerceptionElement, ...] = ()
    last_action: ActionResult | None = None
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
        return UIState(
            application=self.application,
            window=self.window,
            page=self.page,
            elements=self.elements,
            dialogs=self.dialogs,
            notifications=self.notifications,
            last_action=action,
            last_change=self.last_change,
            uia_snapshot=self.uia_snapshot,
        )
