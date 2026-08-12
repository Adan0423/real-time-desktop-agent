from __future__ import annotations

from rtda.actions.win32_input import Win32SendInputBackend
from rtda.models.actions import ActionCommand, ActionRisk, ActionStatus, ActionType, ResolvedAction


def test_win32_input_dry_run() -> None:
    backend = Win32SendInputBackend(dry_run=True)
    cmd = ActionCommand(action=ActionType.CLICK, target="Button")
    resolved = ResolvedAction(command=cmd, risk=ActionRisk.SAFE, x=100, y=200)

    res = backend.execute(resolved)
    assert res.status == ActionStatus.DRY_RUN
    assert res.metadata["backend"] == "win32_send_input"
    assert res.metadata["x"] == 100
    assert res.metadata["y"] == 200
