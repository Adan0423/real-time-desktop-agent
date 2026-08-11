from __future__ import annotations

from dataclasses import dataclass

from rtda.actions.engine import ActionEngine
from rtda.agent.planner import ActionPlan, RuleBasedPlanner
from rtda.agent.recovery import RecoveryManager, RecoveryStep
from rtda.agent.verifier import VerificationResult, Verifier
from rtda.models.actions import ActionResult
from rtda.models.state import UIState
from rtda.state.state_machine import AgentPhase, StateMachine
from rtda.state.state_store import StateStore


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    plan: ActionPlan
    action_results: tuple[ActionResult, ...]
    verification: VerificationResult | None
    recovery: RecoveryStep | None
    final_state: UIState


class AgentExecutor:
    def __init__(
        self,
        *,
        state_store: StateStore | None = None,
        planner: RuleBasedPlanner | None = None,
        action_engine: ActionEngine | None = None,
        verifier: Verifier | None = None,
        recovery: RecoveryManager | None = None,
    ) -> None:
        self.state_store = state_store or StateStore()
        self.planner = planner or RuleBasedPlanner()
        self.action_engine = action_engine or ActionEngine()
        self.verifier = verifier or Verifier()
        self.recovery = recovery or RecoveryManager()
        self.machine = StateMachine()

    def run_once(self, goal: str, *, expected_text: str | None = None) -> AgentRunResult:
        self.machine.transition(AgentPhase.OBSERVE)
        before = self.state_store.get()
        self.machine.transition(AgentPhase.UNDERSTAND)
        self.machine.transition(AgentPhase.PLAN)
        plan = self.planner.plan(before, goal)
        if plan.empty:
            self.machine.transition(AgentPhase.DONE)
            return AgentRunResult(plan, (), None, None, before)

        self.machine.transition(AgentPhase.ACT)
        # Phase 7 executes only one action, then verifies before continuing.
        action_result = self.action_engine.execute(plan.actions[0])
        after = before.with_action(action_result)
        self.state_store.set(after)

        self.machine.transition(AgentPhase.VERIFY)
        verification = self.verifier.verify(before, after, action_result, expected_text=expected_text)
        recovery_step = None
        if verification.success:
            self.machine.transition(AgentPhase.DONE)
        else:
            self.machine.transition(AgentPhase.RECOVER)
            recovery_step = self.recovery.recover(verification)
            self.machine.transition(AgentPhase.DONE)
        return AgentRunResult(plan, (action_result,), verification, recovery_step, after)
