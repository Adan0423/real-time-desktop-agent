from __future__ import annotations

from rtda.actions.engine import ActionEngine
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.agent.executor import AgentExecutor
from rtda.models.perception import BoundingBox, PerceptionElement
from rtda.models.state import UIState
from rtda.state.state_store import StateStore


def test_agent_runs_one_action_then_verifies() -> None:
    state = UIState(
        elements=(
            PerceptionElement(
                type="ButtonControl",
                text="Guardar",
                bbox=BoundingBox(0, 0, 20, 20),
                confidence=1.0,
                source="uia",
            ),
        )
    )
    agent = AgentExecutor(
        state_store=StateStore(state),
        action_engine=ActionEngine(executor=PyAutoGUIActionExecutor(dry_run=True)),
    )

    result = agent.run_once("click Guardar")

    assert result.plan.actions
    assert result.action_results[0].status == "dry_run"
    assert result.verification is not None
    assert result.verification.success is True
