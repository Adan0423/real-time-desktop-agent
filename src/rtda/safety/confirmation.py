from __future__ import annotations

from dataclasses import dataclass, field

from rtda.models.actions import ActionCommand


@dataclass(slots=True)
class ConfirmationManager:
    confirmed_tokens: set[str] = field(default_factory=set)

    def token_for(self, command: ActionCommand) -> str:
        target = command.target or ""
        value = command.value or ""
        return f"{command.action}:{target}:{value}"

    def confirm(self, command: ActionCommand) -> str:
        token = self.token_for(command)
        self.confirmed_tokens.add(token)
        return token

    def is_confirmed(self, command: ActionCommand) -> bool:
        return self.token_for(command) in self.confirmed_tokens
