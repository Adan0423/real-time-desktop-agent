from __future__ import annotations

from dataclasses import dataclass

from rtda.models.actions import ActionCommand, ActionType
from rtda.models.state import UIState


@dataclass(frozen=True, slots=True)
class ActionPlan:
    goal: str
    actions: tuple[ActionCommand, ...]
    rationale: str

    @property
    def empty(self) -> bool:
        return not self.actions


class RuleBasedPlanner:
    """Small deterministic planner for early phases."""

    def plan(self, state: UIState, goal: str) -> ActionPlan:
        normalized = goal.strip()
        lower = normalized.casefold()
        if not normalized:
            return ActionPlan(goal=goal, actions=(), rationale="empty goal")
        if lower.startswith("click "):
            target = normalized[6:].strip().strip('"')
            return ActionPlan(goal=goal, actions=(ActionCommand(action=ActionType.CLICK, target=target),), rationale="click goal")
        if lower.startswith("type "):
            text = normalized[5:].strip()
            return ActionPlan(goal=goal, actions=(ActionCommand(action=ActionType.TYPE, value=text),), rationale="type goal")
        if lower.startswith("inspect"):
            return ActionPlan(goal=goal, actions=(ActionCommand(action=ActionType.INSPECT),), rationale="inspect goal")
        matches = state.find_elements(normalized)
        if matches:
            return ActionPlan(
                goal=goal,
                actions=(ActionCommand(action=ActionType.CLICK, target=normalized),),
                rationale="matched visible element",
            )
        return ActionPlan(goal=goal, actions=(), rationale="no rule matched")
