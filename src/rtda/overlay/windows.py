from __future__ import annotations

import ctypes
from ctypes import wintypes

from rtda.overlay.geometry import OverlayRect

DWMWA_EXTENDED_FRAME_BOUNDS = 9


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def find_window_rect_by_title(title_substring: str) -> OverlayRect | None:
    title_substring = title_substring.strip().casefold()
    if not title_substring:
        return None
    hwnd = _find_window_handle(title_substring)
    if hwnd is None:
        return None
    return _visible_window_rect(hwnd) or _window_rect(hwnd)


def _find_window_handle(title_substring: str) -> int | None:
    user32 = ctypes.windll.user32
    matches: list[int] = []

    @EnumWindowsProc
    def enum_proc(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title_substring in buffer.value.casefold():
            matches.append(hwnd)
            return False
        return True

    user32.EnumWindows(enum_proc, 0)
    return matches[0] if matches else None


def _visible_window_rect(hwnd: int) -> OverlayRect | None:
    try:
        dwmapi = ctypes.windll.dwmapi
    except AttributeError:
        return None
    rect = RECT()
    result = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    if result != 0:
        return None
    return _rect_to_overlay(rect)


def _window_rect(hwnd: int) -> OverlayRect | None:
    rect = RECT()
    if not ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        return None
    return _rect_to_overlay(rect)


def _rect_to_overlay(rect: RECT) -> OverlayRect | None:
    overlay = OverlayRect(int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))
    return overlay if overlay.valid else None
