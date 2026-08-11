from __future__ import annotations

from dataclasses import dataclass

from rtda.agent.verifier import VerificationResult
from rtda.models.actions import ActionCommand, ActionType


@dataclass(frozen=True, slots=True)
class RecoveryStep:
    reason: str
    command: ActionCommand | None


class RecoveryManager:
    def recover(self, verification: VerificationResult) -> RecoveryStep:
        if "not found" in verification.message:
            return RecoveryStep("target missing; inspect UI again", ActionCommand(action=ActionType.INSPECT))
        if "blocked" in verification.message or "requires confirmation" in verification.message:
            return RecoveryStep("action blocked by safety policy", None)
        return RecoveryStep("observe again", ActionCommand(action=ActionType.INSPECT))
