from rtda.models.actions import ActionCommand, ActionType


def click(target: str) -> ActionCommand:
    return ActionCommand(action=ActionType.CLICK, target=target)


def move(target: str) -> ActionCommand:
    return ActionCommand(action=ActionType.MOVE, target=target)
