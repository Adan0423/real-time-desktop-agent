from __future__ import annotations

from dataclasses import dataclass

from rtda.models.actions import ActionCommand, ActionResult, ActionType
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
    """Deterministic rule-based planner.

    Supports:
    - Single-action commands: ``click X``, ``type X``, ``inspect``, ``hotkey X+Y``
    - Compound commands joined by `` and `` or ``;``: decomposed into multiple actions
    - History-aware: skips actions whose targets previously failed
    - Fallback to INSPECT when no rule matches (triggers an observation cycle)
    """

    _CONJUNCTIONS = (" and then ", " and ", " then ", "; ")

    def plan(
        self,
        state: UIState,
        goal: str,
        history: tuple[ActionResult, ...] | None = None,
    ) -> ActionPlan:
        normalized = goal.strip()
        if not normalized:
            return ActionPlan(goal=goal, actions=(), rationale="empty goal")

        # Build set of recently-failed targets to avoid repeating them
        failed_targets: set[str] = set()
        completed_count = 0
        for result in (history or ()):
            from rtda.models.actions import ActionStatus
            if result.status in (ActionStatus.FAILED, ActionStatus.BLOCKED):
                t = result.command.target
                if t:
                    failed_targets.add(t.casefold())
            elif result.status in (ActionStatus.SUCCESS, ActionStatus.DRY_RUN):
                completed_count += 1

        # Try to decompose compound instructions
        parts = self._split_compound(normalized)
        if len(parts) > 1:
            actions: list[ActionCommand] = []
            for part in parts:
                cmd = self._parse_single(part.strip(), state, failed_targets)
                if cmd is not None:
                    actions.append(cmd)
            # Skip already completed actions from compound goal
            remaining_actions = actions[completed_count:]
            if remaining_actions:
                return ActionPlan(
                    goal=goal,
                    actions=tuple(remaining_actions),
                    rationale=f"compound goal ({len(remaining_actions)} actions remaining)",
                )
            elif actions:
                return ActionPlan(goal=goal, actions=(), rationale="all compound actions completed")

        # Single instruction: if already completed 1+ actions for this single goal, we are done
        if completed_count > 0:
            return ActionPlan(goal=goal, actions=(), rationale="single goal action completed")

        cmd = self._parse_single(normalized, state, failed_targets)
        if cmd is not None:
            return ActionPlan(goal=goal, actions=(cmd,), rationale=self._rationale(cmd))

        # Fallback: INSPECT to gather more UI information
        return ActionPlan(
            goal=goal,
            actions=(ActionCommand(action=ActionType.INSPECT),),
            rationale="no rule matched; inspecting UI for more context",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _split_compound(self, text: str) -> list[str]:
        lower = text.casefold()
        for sep in self._CONJUNCTIONS:
            if sep in lower:
                idx = lower.index(sep)
                return [text[:idx], text[idx + len(sep):]]
        return [text]

    def _parse_single(
        self,
        text: str,
        state: UIState,
        failed_targets: set[str],
    ) -> ActionCommand | None:
        lower = text.casefold()

        if lower.startswith("click "):
            target = text[6:].strip().strip('"')
            if target.casefold() in failed_targets:
                return None
            return ActionCommand(action=ActionType.CLICK, target=target)

        if lower.startswith("type "):
            value = text[5:].strip()
            return ActionCommand(action=ActionType.TYPE, value=value)

        if lower.startswith("press "):
            value = text[6:].strip()
            return ActionCommand(action=ActionType.PRESS, value=value)

        if lower.startswith("hotkey "):
            keys_str = text[7:].strip()
            keys = [k.strip() for k in keys_str.replace("+", " ").split() if k.strip()]
            return ActionCommand(action=ActionType.HOTKEY, keys=keys)

        if lower.startswith("scroll"):
            amount_str = text[6:].strip()
            try:
                amount = int(amount_str)
            except ValueError:
                amount = -3 if "down" in lower else 3
            return ActionCommand(action=ActionType.SCROLL, amount=amount)

        if lower.startswith("navigate ") or lower.startswith("open "):
            value = text.split(" ", 1)[1].strip()
            return ActionCommand(action=ActionType.NAVIGATE, value=value)

        if lower.startswith("inspect") or lower == "observe":
            return ActionCommand(action=ActionType.INSPECT)

        # Match against visible state elements
        matches = state.find_elements(text)
        if matches:
            target = text
            if target.casefold() not in failed_targets:
                return ActionCommand(action=ActionType.CLICK, target=target)

        return None

    @staticmethod
    def _rationale(cmd: ActionCommand) -> str:
        if cmd.action == ActionType.CLICK:
            return f"click goal: {cmd.target!r}"
        if cmd.action == ActionType.TYPE:
            return f"type goal: {cmd.value!r}"
        if cmd.action == ActionType.INSPECT:
            return "inspect goal"
        return f"{cmd.action} goal"

