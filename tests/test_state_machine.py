from __future__ import annotations

import pytest

from rtda.state.state_machine import AgentPhase, StateMachine


def test_state_machine_rejects_invalid_transition() -> None:
    machine = StateMachine()

    with pytest.raises(ValueError):
        machine.transition(AgentPhase.ACT)
