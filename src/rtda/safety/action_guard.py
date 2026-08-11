from __future__ import annotations

from dataclasses import dataclass

from rtda.models.actions import ActionCommand, ActionRisk
from rtda.safety.confirmation import ConfirmationManager
from rtda.safety.policy import ActionPolicy


@dataclass(slots=True)
class ActionGuard:
    policy: ActionPolicy
    confirmations: ConfirmationManager

    def classify(self, command: ActionCommand) -> ActionRisk:
        return self.policy.classify(command)

    def allowed(self, command: ActionCommand) -> tuple[bool, ActionRisk, str]:
        risk = self.classify(command)
        if risk == ActionRisk.SAFE:
            return True, risk, "safe action"
        if risk == ActionRisk.MODERATE:
            return self.policy.allow_moderate, risk, "moderate action allowed"
        if self.policy.allow_dangerous_with_confirmation and self.confirmations.is_confirmed(command):
            return True, risk, "dangerous action confirmed"
        return False, risk, "dangerous action requires confirmation"
