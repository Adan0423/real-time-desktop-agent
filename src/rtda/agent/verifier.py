from __future__ import annotations

from dataclasses import dataclass

from rtda.models.actions import ActionResult, ActionStatus
from rtda.models.state import UIState


@dataclass(frozen=True, slots=True)
class VerificationResult:
    success: bool
    message: str


class Verifier:
    def verify(self, before: UIState, after: UIState, action: ActionResult, expected_text: str | None = None) -> VerificationResult:
        if action.status in (ActionStatus.FAILED, ActionStatus.BLOCKED):
            return VerificationResult(False, action.message)
        if expected_text:
            if after.find_elements(expected_text):
                return VerificationResult(True, "expected text found")
            return VerificationResult(False, "expected text not found")
        if after.timestamp >= before.timestamp:
            return VerificationResult(True, "state updated after action")
        return VerificationResult(False, "state did not update")
