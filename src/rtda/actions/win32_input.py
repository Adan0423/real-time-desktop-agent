from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from dataclasses import dataclass

from rtda.actions.interface import ActionExecutor
from rtda.models.actions import ActionResult, ActionStatus, ActionType, ResolvedAction

# ------------------------------------------------------------------
# Win32 C Struct Definitions for SendInput
# ------------------------------------------------------------------

LONG = ctypes.c_long
DWORD = ctypes.c_ulong
WORD = ctypes.c_ushort

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_MAP = {
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "escape": 0x1B,
    "esc": 0x1B,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "win": 0x5B,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", LONG),
        ("dy", LONG),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", WORD),
        ("wScan", WORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", DWORD),
        ("wParamL", WORD),
        ("wParamH", WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", DWORD),
        ("u", _INPUT_UNION),
    ]


def _send_input(inputs: list[INPUT]) -> int:
    n = len(inputs)
    if n == 0:
        return 0
    arr = (INPUT * n)(*inputs)
    return ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _move_cursor(x: int, y: int) -> None:
    ctypes.windll.user32.SetCursorPos(x, y)


def _click_at(x: int, y: int, button: str = "left") -> None:
    _move_cursor(x, y)
    time.sleep(0.01)

    down_flag = MOUSEEVENTF_LEFTDOWN if button == "left" else MOUSEEVENTF_RIGHTDOWN
    up_flag = MOUSEEVENTF_LEFTUP if button == "left" else MOUSEEVENTF_RIGHTUP

    inp_down = INPUT(type=INPUT_MOUSE)
    inp_down.u.mi.dwFlags = down_flag
    inp_up = INPUT(type=INPUT_MOUSE)
    inp_up.u.mi.dwFlags = up_flag

    _send_input([inp_down, inp_up])


def _type_unicode_string(text: str) -> None:
    inputs = []
    for char in text:
        code = ord(char)
        inp_down = INPUT(type=INPUT_KEYBOARD)
        inp_down.u.ki.wScan = code
        inp_down.u.ki.dwFlags = KEYEVENTF_UNICODE

        inp_up = INPUT(type=INPUT_KEYBOARD)
        inp_up.u.ki.wScan = code
        inp_up.u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP

        inputs.extend([inp_down, inp_up])

    if inputs:
        _send_input(inputs)


def _press_vk(vk_code: int) -> None:
    inp_down = INPUT(type=INPUT_KEYBOARD)
    inp_down.u.ki.wVk = vk_code
    inp_down.u.ki.dwFlags = KEYEVENTF_KEYDOWN

    inp_up = INPUT(type=INPUT_KEYBOARD)
    inp_up.u.ki.wVk = vk_code
    inp_up.u.ki.dwFlags = KEYEVENTF_KEYUP

    _send_input([inp_down, inp_up])


@dataclass(slots=True)
class Win32SendInputBackend(ActionExecutor):
    """Ultra-low latency (<20ms) native Windows SendInput action executor.

    Executes mouse clicks, movements, text typing and keyboard events directly
    via Windows user32.dll SendInput C APIs.
    """

    dry_run: bool = False

    def execute(self, action: ResolvedAction) -> ActionResult:
        started = time.perf_counter()
        command = action.command

        if self.dry_run:
            return ActionResult(
                command=command,
                status=ActionStatus.DRY_RUN,
                risk=action.risk,
                message="win32 send_input dry-run accepted",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                resolved_bbox=action.bbox,
                metadata={"x": action.x, "y": action.y, "backend": "win32_send_input"},
            )

        try:
            self._execute_native(action)
        except Exception as exc:
            return ActionResult(
                command=command,
                status=ActionStatus.FAILED,
                risk=action.risk,
                message=f"Win32SendInputError: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                resolved_bbox=action.bbox,
            )

        return ActionResult(
            command=command,
            status=ActionStatus.SUCCESS,
            risk=action.risk,
            message="win32 action executed",
            latency_ms=(time.perf_counter() - started) * 1000.0,
            resolved_bbox=action.bbox,
            metadata={"x": action.x, "y": action.y, "backend": "win32_send_input"},
        )

    def _execute_native(self, action: ResolvedAction) -> None:
        cmd = action.command

        if cmd.action in (ActionType.MOVE, ActionType.HOVER):
            if action.x is not None and action.y is not None:
                _move_cursor(action.x, action.y)

        elif cmd.action == ActionType.CLICK:
            if action.x is not None and action.y is not None:
                _click_at(action.x, action.y, button="left")

        elif cmd.action == ActionType.TYPE:
            if action.x is not None and action.y is not None:
                _click_at(action.x, action.y, button="left")
            if cmd.value:
                _type_unicode_string(cmd.value)

        elif cmd.action == ActionType.PRESS:
            key_name = (cmd.value or (cmd.keys[0] if cmd.keys else "enter")).casefold()
            vk = VK_MAP.get(key_name)
            if vk is not None:
                _press_vk(vk)
            else:
                _type_unicode_string(key_name)

        elif cmd.action == ActionType.HOTKEY:
            if not cmd.keys:
                raise ValueError("hotkey requires keys")
            # Down sequence
            vks = [VK_MAP.get(k.casefold(), 0) for k in cmd.keys]
            for vk in vks:
                if vk:
                    inp = INPUT(type=INPUT_KEYBOARD)
                    inp.u.ki.wVk = vk
                    inp.u.ki.dwFlags = KEYEVENTF_KEYDOWN
                    _send_input([inp])
            time.sleep(0.01)
            # Up sequence (reverse order)
            for vk in reversed(vks):
                if vk:
                    inp = INPUT(type=INPUT_KEYBOARD)
                    inp.u.ki.wVk = vk
                    inp.u.ki.dwFlags = KEYEVENTF_KEYUP
                    _send_input([inp])

        elif cmd.action == ActionType.SCROLL:
            amount = (cmd.amount or 0) * 120
            inp = INPUT(type=INPUT_MOUSE)
            inp.u.mi.dwFlags = MOUSEEVENTF_WHEEL
            inp.u.mi.mouseData = amount if amount >= 0 else (0x100000000 + amount)
            _send_input([inp])

        elif cmd.action == ActionType.NAVIGATE:
            import subprocess
            target = cmd.value or cmd.target or ""
            if target:
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)

        else:
            raise ValueError(f"unsupported win32 action: {cmd.action}")
