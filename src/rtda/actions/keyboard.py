from rtda.models.actions import ActionCommand, ActionType


def type_text(target: str | None, value: str) -> ActionCommand:
    return ActionCommand(action=ActionType.TYPE, target=target, value=value)


def press(key: str) -> ActionCommand:
    return ActionCommand(action=ActionType.PRESS, value=key)


def hotkey(*keys: str) -> ActionCommand:
    return ActionCommand(action=ActionType.HOTKEY, keys=list(keys))
