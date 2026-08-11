from rtda.models.actions import ActionCommand, ActionType


def scroll(amount: int) -> ActionCommand:
    return ActionCommand(action=ActionType.SCROLL, amount=amount)
