from __future__ import annotations

from rtda.actions.engine import ActionEngine
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.actions.resolver import TargetResolver
from rtda.models.actions import ActionCommand, ActionStatus, ActionType
from rtda.models.perception import BoundingBox, PerceptionElement


def test_action_engine_resolves_semantic_target_in_dry_run() -> None:
    element = PerceptionElement(
        type="ButtonControl",
        text="Guardar",
        bbox=BoundingBox(10, 20, 30, 40),
        confidence=0.9,
        source="uia",
    )
    engine = ActionEngine(
        resolver=TargetResolver((element,)),
        executor=PyAutoGUIActionExecutor(dry_run=True),
    )

    result = engine.execute(ActionCommand(action=ActionType.CLICK, target="Guardar"))

    assert result.status == ActionStatus.DRY_RUN
    assert result.resolved_bbox == element.bbox
    assert result.metadata["x"] == 20
    assert result.metadata["y"] == 30


def test_action_engine_blocks_dangerous_action_without_confirmation() -> None:
    engine = ActionEngine()

    result = engine.execute(ActionCommand(action=ActionType.DELETE, target="file"))

    assert result.status == ActionStatus.BLOCKED
    assert "requires confirmation" in result.message
