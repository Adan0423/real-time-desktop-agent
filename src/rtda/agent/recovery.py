from __future__ import annotations

from dataclasses import dataclass

from rtda.agent.verifier import VerificationResult
from rtda.models.actions import ActionCommand, ActionType


@dataclass(frozen=True, slots=True)
class RecoveryStep:
    reason: str
    command: ActionCommand | None
    execute: bool = True  # if True the executor will run this command immediately


class RecoveryManager:
    """Selects a recovery action based on what went wrong.

    Each strategy returns a RecoveryStep with execute=True so that
    AgentExecutor.run_task() actually runs it on the next cycle.
    """

    def recover(self, verification: VerificationResult) -> RecoveryStep:
        msg = verification.message.casefold()

        # Element not found → inspect to refresh UI tree
        if "not found" in msg or "no rule matched" in msg:
            return RecoveryStep(
                reason="target missing; refreshing UI snapshot",
                command=ActionCommand(action=ActionType.INSPECT),
            )

        # Blocked by safety policy → no automatic action, needs confirmation
        if "blocked" in msg or "requires confirmation" in msg or "dangerous" in msg:
            return RecoveryStep(
                reason="action blocked by safety policy; awaiting confirmation",
                command=None,
                execute=False,
            )

        # Dialog or popup appeared → try Escape to dismiss
        if verification.window_changed:
            return RecoveryStep(
                reason="unexpected window/dialog appeared; sending Escape",
                command=ActionCommand(action=ActionType.PRESS, value="escape"),
            )

        # UI frozen or no change detected → scroll to reveal more content
        if "did not change" in msg or "stable" in msg:
            return RecoveryStep(
                reason="UI unchanged; scrolling down to reveal more content",
                command=ActionCommand(action=ActionType.SCROLL, amount=-3),
            )

        # Default: re-inspect
        return RecoveryStep(
            reason="unknown failure; re-inspecting UI",
            command=ActionCommand(action=ActionType.INSPECT),
        )

