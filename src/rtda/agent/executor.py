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
    observe_ms: float = 0.0
    plan_ms: float = 0.0
    act_ms: float = 0.0
    verify_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class AgentTaskResult:
    goal: str
    success: bool
    steps: int
    cycles: list[AgentRunResult] = field(default_factory=list)
    final_state: UIState = field(default_factory=UIState)
    elapsed_ms: float = 0.0
    stop_reason: str = ""
    telemetry: dict[str, float] = field(default_factory=dict)


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
            AgentTaskResult with all cycles, final state, telemetry and stop reason.
        """
        started = time.perf_counter()
        cycles: list[AgentRunResult] = []
        self.state_store.set(UIState())
        current_state = self.state_store.get()

        for step in range(max_steps):
            cycle_start = time.perf_counter()

            # ── OBSERVE ──────────────────────────────────────────────
            self.machine.transition(AgentPhase.OBSERVE)
            t_obs0 = time.perf_counter()
            observed = self.observer.observe(window_title=window_title)
            current_state = current_state.with_observation(
                focused_window=observed.focused_window,
                application=observed.application,
                elements=observed.elements,
                uia_snapshot=observed.uia_snapshot,
            )
            self.state_store.set(current_state)
            before = current_state
            observe_ms = (time.perf_counter() - t_obs0) * 1000.0

            # ── UNDERSTAND + PLAN ─────────────────────────────────────
            self.machine.transition(AgentPhase.UNDERSTAND)
            self.machine.transition(AgentPhase.PLAN)
            t_plan0 = time.perf_counter()
            plan = self.planner.plan(before, goal, history=before.action_history)
            plan_ms = (time.perf_counter() - t_plan0) * 1000.0

            if plan.empty:
                self.machine.transition(AgentPhase.DONE)
                break

            # ── ACT (one action per cycle, then verify) ───────────────
            self.machine.transition(AgentPhase.ACT)
            t_act0 = time.perf_counter()
            action_cmd = plan.actions[0]
            action_result = self.action_engine.execute(action_cmd)
            after = before.with_action(action_result)
            self.state_store.set(after)
            act_ms = (time.perf_counter() - t_act0) * 1000.0

            # ── VERIFY ────────────────────────────────────────────────
            self.machine.transition(AgentPhase.VERIFY)
            t_ver0 = time.perf_counter()

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
            verify_ms = (time.perf_counter() - t_ver0) * 1000.0
            cycle_total_ms = (time.perf_counter() - cycle_start) * 1000.0

            recovery_step: RecoveryStep | None = None

            if verification.success:
                current_state = after
                self.machine.transition(AgentPhase.DONE)
                run_res = AgentRunResult(
                    plan=plan,
                    action_results=(action_result,),
                    verification=verification,
                    recovery=None,
                    final_state=after,
                    observe_ms=observe_ms,
                    plan_ms=plan_ms,
                    act_ms=act_ms,
                    verify_ms=verify_ms,
                    total_ms=cycle_total_ms,
                )
                cycles.append(run_res)

                # If expected_text found → task complete
                if expected_text and after.find_elements(expected_text):
                    total_ms = (time.perf_counter() - started) * 1000.0
                    return AgentTaskResult(
                        goal=goal,
                        success=True,
                        steps=step + 1,
                        cycles=cycles,
                        final_state=after,
                        elapsed_ms=total_ms,
                        stop_reason="expected text found",
                        telemetry=self._aggregate_telemetry(cycles, total_ms),
                    )
            else:
                # ── RECOVER ───────────────────────────────────────────
                self.machine.transition(AgentPhase.RECOVER)
                recovery_step = self.recovery.recover(verification)
                run_res = AgentRunResult(
                    plan=plan,
                    action_results=(action_result,),
                    verification=verification,
                    recovery=recovery_step,
                    final_state=after,
                    observe_ms=observe_ms,
                    plan_ms=plan_ms,
                    act_ms=act_ms,
                    verify_ms=verify_ms,
                    total_ms=cycle_total_ms,
                )
                cycles.append(run_res)

                # Execute recovery command if applicable
                if recovery_step.execute and recovery_step.command is not None:
                    self.action_engine.execute(recovery_step.command)

                # Safety-blocked actions stop the task
                if not recovery_step.execute:
                    self.machine.transition(AgentPhase.DONE)
                    total_ms = (time.perf_counter() - started) * 1000.0
                    return AgentTaskResult(
                        goal=goal,
                        success=False,
                        steps=step + 1,
                        cycles=cycles,
                        final_state=after,
                        elapsed_ms=total_ms,
                        stop_reason=recovery_step.reason,
                        telemetry=self._aggregate_telemetry(cycles, total_ms),
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
            telemetry=self._aggregate_telemetry(cycles, elapsed_ms),
        )

    @staticmethod
    def _aggregate_telemetry(cycles: list[AgentRunResult], total_elapsed_ms: float) -> dict[str, float]:
        if not cycles:
            return {"elapsed_ms": total_elapsed_ms, "avg_cycle_ms": 0.0}
        n = len(cycles)
        avg_obs = sum(c.observe_ms for c in cycles) / n
        avg_plan = sum(c.plan_ms for c in cycles) / n
        avg_act = sum(c.act_ms for c in cycles) / n
        avg_ver = sum(c.verify_ms for c in cycles) / n
        avg_cycle = sum(c.total_ms for c in cycles) / n
        return {
            "elapsed_ms": round(total_elapsed_ms, 2),
            "avg_observe_ms": round(avg_obs, 2),
            "avg_plan_ms": round(avg_plan, 2),
            "avg_act_ms": round(avg_act, 2),
            "avg_verify_ms": round(avg_ver, 2),
            "avg_cycle_ms": round(avg_cycle, 2),
        }

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

