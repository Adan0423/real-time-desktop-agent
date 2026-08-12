from __future__ import annotations

import time
from dataclasses import dataclass, field

from rtda.actions.engine import ActionEngine
from rtda.agent.observer import AgentObserver
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


@dataclass
class AgentTaskResult:
    goal: str
    success: bool
    steps: int
    cycles: list[AgentRunResult] = field(default_factory=list)
    final_state: UIState = field(default_factory=UIState)
    elapsed_ms: float = 0.0
    stop_reason: str = ""


class AgentExecutor:
    def __init__(
        self,
        *,
        state_store: StateStore | None = None,
        planner: RuleBasedPlanner | None = None,
        action_engine: ActionEngine | None = None,
        verifier: Verifier | None = None,
        recovery: RecoveryManager | None = None,
        observer: AgentObserver | None = None,
    ) -> None:
        self.state_store = state_store or StateStore()
        self.planner = planner or RuleBasedPlanner()
        self.action_engine = action_engine or ActionEngine()
        self.verifier = verifier or Verifier()
        self.recovery = recovery or RecoveryManager()
        self.observer = observer or AgentObserver()
        self.machine = StateMachine()

    # ------------------------------------------------------------------
    # run_task — full multi-step loop
    # ------------------------------------------------------------------

    def run_task(
        self,
        goal: str,
        *,
        max_steps: int = 10,
        expected_text: str | None = None,
        window_title: str | None = None,
    ) -> AgentTaskResult:
        """Execute a task by looping observe→plan→act→verify until done.

        Args:
            goal:          Natural-language instruction for the planner.
            max_steps:     Maximum number of act cycles (safety cap).
            expected_text: If given, success is confirmed when this text
                           appears in the UI state.
            window_title:  Optional target window; defaults to foreground window.

        Returns:
            AgentTaskResult with all cycles, final state and stop reason.
        """
        started = time.perf_counter()
        cycles: list[AgentRunResult] = []
        current_state = self.state_store.get()

        for step in range(max_steps):
            # ── OBSERVE ──────────────────────────────────────────────
            self.machine.transition(AgentPhase.OBSERVE)
            observed = self.observer.observe(window_title=window_title)
            current_state = current_state.with_observation(
                focused_window=observed.focused_window,
                application=observed.application,
                elements=observed.elements,
                uia_snapshot=observed.uia_snapshot,
            )
            self.state_store.set(current_state)
            before = current_state

            # ── UNDERSTAND + PLAN ─────────────────────────────────────
            self.machine.transition(AgentPhase.UNDERSTAND)
            self.machine.transition(AgentPhase.PLAN)
            plan = self.planner.plan(before, goal, history=before.action_history)

            if plan.empty:
                self.machine.transition(AgentPhase.DONE)
                break

            # ── ACT (one action per cycle, then verify) ───────────────
            self.machine.transition(AgentPhase.ACT)
            action_cmd = plan.actions[0]
            action_result = self.action_engine.execute(action_cmd)
            after = before.with_action(action_result)
            self.state_store.set(after)

            # ── VERIFY ────────────────────────────────────────────────
            self.machine.transition(AgentPhase.VERIFY)

            # Take a fresh observation for post-action state
            post_observed = self.observer.observe(window_title=window_title)
            after = after.with_observation(
                focused_window=post_observed.focused_window,
                application=post_observed.application,
                elements=post_observed.elements,
                uia_snapshot=post_observed.uia_snapshot,
            )
            self.state_store.set(after)

            verification = self.verifier.verify(
                before, after, action_result, expected_text=expected_text
            )
            recovery_step: RecoveryStep | None = None

            if verification.success:
                current_state = after
                self.machine.transition(AgentPhase.DONE)
                cycles.append(AgentRunResult(plan, (action_result,), verification, None, after))

                # If expected_text found → task complete
                if expected_text and after.find_elements(expected_text):
                    return AgentTaskResult(
                        goal=goal,
                        success=True,
                        steps=step + 1,
                        cycles=cycles,
                        final_state=after,
                        elapsed_ms=(time.perf_counter() - started) * 1000.0,
                        stop_reason="expected text found",
                    )
            else:
                # ── RECOVER ───────────────────────────────────────────
                self.machine.transition(AgentPhase.RECOVER)
                recovery_step = self.recovery.recover(verification)
                cycles.append(AgentRunResult(plan, (action_result,), verification, recovery_step, after))

                # Execute recovery command if applicable
                if recovery_step.execute and recovery_step.command is not None:
                    self.action_engine.execute(recovery_step.command)

                # Safety-blocked actions stop the task
                if not recovery_step.execute:
                    self.machine.transition(AgentPhase.DONE)
                    return AgentTaskResult(
                        goal=goal,
                        success=False,
                        steps=step + 1,
                        cycles=cycles,
                        final_state=after,
                        elapsed_ms=(time.perf_counter() - started) * 1000.0,
                        stop_reason=recovery_step.reason,
                    )

                current_state = after
                self.machine.transition(AgentPhase.DONE)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        final = self.state_store.get()
        last_cycle_ok = bool(cycles) and cycles[-1].verification is not None and cycles[-1].verification.success
        return AgentTaskResult(
            goal=goal,
            success=last_cycle_ok,
            steps=len(cycles),
            cycles=cycles,
            final_state=final,
            elapsed_ms=elapsed_ms,
            stop_reason="max_steps reached" if len(cycles) >= max_steps else "plan exhausted",
        )

    # ------------------------------------------------------------------
    # run_once — kept for backward compat and single-shot MCP calls
    # ------------------------------------------------------------------

    def run_once(self, goal: str, *, expected_text: str | None = None) -> AgentRunResult:
        self.machine.transition(AgentPhase.OBSERVE)
        before = self.state_store.get()
        self.machine.transition(AgentPhase.UNDERSTAND)
        self.machine.transition(AgentPhase.PLAN)
        plan = self.planner.plan(before, goal, history=before.action_history)
        if plan.empty:
            self.machine.transition(AgentPhase.DONE)
            return AgentRunResult(plan, (), None, None, before)

        self.machine.transition(AgentPhase.ACT)
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
            if recovery_step.execute and recovery_step.command is not None:
                self.action_engine.execute(recovery_step.command)
            self.machine.transition(AgentPhase.DONE)
        return AgentRunResult(plan, (action_result,), verification, recovery_step, after)

