from __future__ import annotations

import time
from dataclasses import dataclass

from rtda.models.actions import ActionResult, ActionStatus
from rtda.models.state import UIState


@dataclass(frozen=True, slots=True)
class VerificationResult:
    success: bool
    message: str
    changed_elements: int = 0
    window_changed: bool = False


class Verifier:
    """Verifies whether an action had the expected effect on the UI.

    Strategy (in order):
    1. If the action was FAILED or BLOCKED → immediate failure.
    2. If ``expected_text`` is provided → search for it in after-state elements.
    3. Compare UIA element sets before/after: if count or names differ → success.
    4. Detect foreground-window change (e.g. a dialog opened).
    5. Fallback: wait briefly and re-check element count.
    """

    def __init__(self, wait_ms: float = 300.0) -> None:
        self.wait_ms = wait_ms

    def verify(
        self,
        before: UIState,
        after: UIState,
        action: ActionResult,
        *,
        expected_text: str | None = None,
    ) -> VerificationResult:
        # 1. Hard failure from executor
        if action.status in (ActionStatus.FAILED, ActionStatus.BLOCKED):
            return VerificationResult(False, action.message)

        # DRY_RUN is always considered a pass (simulation mode)
        if action.status == ActionStatus.DRY_RUN:
            return VerificationResult(True, "dry-run accepted", changed_elements=0)

        # 2. Wait briefly for UI to settle
        if self.wait_ms > 0:
            time.sleep(self.wait_ms / 1000.0)

        # 3. Expected text check (highest priority)
        if expected_text:
            if after.find_elements(expected_text):
                return VerificationResult(True, f"expected text found: {expected_text!r}")
            return VerificationResult(False, f"expected text not found: {expected_text!r}")

        # 4. Window changed (e.g. dialog opened, new window)
        window_changed = (
            after.focused_window is not None
            and before.focused_window is not None
            and after.focused_window != before.focused_window
        )
        if window_changed:
            return VerificationResult(
                True,
                f"window changed: {before.focused_window!r} → {after.focused_window!r}",
                window_changed=True,
            )

        # 5. UIA element diff — names and count
        before_names = frozenset(
            el.text for el in before.elements if el.text
        )
        after_names = frozenset(
            el.text for el in after.elements if el.text
        )
        new_elements = len(after_names - before_names)
        removed_elements = len(before_names - after_names)
        changed = new_elements + removed_elements

        if changed > 0:
            return VerificationResult(
                True,
                f"UI changed: +{new_elements} new, -{removed_elements} removed elements",
                changed_elements=changed,
            )

        count_before = len(before.elements)
        count_after = len(after.elements)
        if count_before != count_after:
            return VerificationResult(
                True,
                f"element count changed: {count_before} → {count_after}",
                changed_elements=abs(count_after - count_before),
            )

        # 6. Fallback: action succeeded but UI looks unchanged
        #    (e.g. typed text into a field — text itself is in the field)
        if action.status == ActionStatus.SUCCESS:
            return VerificationResult(
                True,
                "action succeeded; UI appears stable (no visible change detected)",
            )

        return VerificationResult(False, "state did not change after action")

