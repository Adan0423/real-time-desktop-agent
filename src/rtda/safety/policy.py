from __future__ import annotations

from dataclasses import dataclass, field

from rtda.models.actions import ActionCommand, ActionRisk, ActionType


DEFAULT_RISK_MAP: dict[ActionType, ActionRisk] = {
    ActionType.MOVE: ActionRisk.SAFE,
    ActionType.HOVER: ActionRisk.SAFE,
    ActionType.READ: ActionRisk.SAFE,
    ActionType.INSPECT: ActionRisk.SAFE,
    ActionType.SCROLL: ActionRisk.SAFE,
    ActionType.CLICK: ActionRisk.MODERATE,
    ActionType.TYPE: ActionRisk.MODERATE,
    ActionType.PRESS: ActionRisk.MODERATE,
    ActionType.HOTKEY: ActionRisk.MODERATE,
    ActionType.NAVIGATE: ActionRisk.MODERATE,
    ActionType.DELETE: ActionRisk.DANGEROUS,
    ActionType.PUBLISH: ActionRisk.DANGEROUS,
    ActionType.SEND: ActionRisk.DANGEROUS,
    ActionType.PURCHASE: ActionRisk.DANGEROUS,
    ActionType.SUBMIT: ActionRisk.DANGEROUS,
}


@dataclass(frozen=True, slots=True)
class ActionPolicy:
    risk_map: dict[ActionType, ActionRisk] = field(default_factory=lambda: dict(DEFAULT_RISK_MAP))
    allow_moderate: bool = True
    allow_dangerous_with_confirmation: bool = True

    def classify(self, command: ActionCommand) -> ActionRisk:
        return self.risk_map.get(command.action, ActionRisk.DANGEROUS)
