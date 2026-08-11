from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgentPhase(StrEnum):
    IDLE = "idle"
    OBSERVE = "observe"
    UNDERSTAND = "understand"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    RECOVER = "recover"
    DONE = "done"


ALLOWED_TRANSITIONS = {
    AgentPhase.IDLE: {AgentPhase.OBSERVE},
    AgentPhase.OBSERVE: {AgentPhase.UNDERSTAND, AgentPhase.RECOVER},
    AgentPhase.UNDERSTAND: {AgentPhase.PLAN, AgentPhase.RECOVER},
    AgentPhase.PLAN: {AgentPhase.ACT, AgentPhase.DONE, AgentPhase.RECOVER},
    AgentPhase.ACT: {AgentPhase.VERIFY, AgentPhase.RECOVER},
    AgentPhase.VERIFY: {AgentPhase.DONE, AgentPhase.OBSERVE, AgentPhase.RECOVER},
    AgentPhase.RECOVER: {AgentPhase.OBSERVE, AgentPhase.DONE},
    AgentPhase.DONE: {AgentPhase.OBSERVE},
}


@dataclass(slots=True)
class StateMachine:
    phase: AgentPhase = AgentPhase.IDLE

    def transition(self, next_phase: AgentPhase) -> None:
        if next_phase not in ALLOWED_TRANSITIONS[self.phase]:
            raise ValueError(f"invalid transition: {self.phase} -> {next_phase}")
        self.phase = next_phase
