from rtda.models.actions import ActionCommand, ActionType


def navigate(value: str) -> ActionCommand:
    return ActionCommand(action=ActionType.NAVIGATE, value=value)
