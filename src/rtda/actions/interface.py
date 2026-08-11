from __future__ import annotations

from abc import ABC, abstractmethod

from rtda.models.actions import ActionResult, ResolvedAction


class ActionExecutor(ABC):
    @abstractmethod
    def execute(self, action: ResolvedAction) -> ActionResult:
        raise NotImplementedError
