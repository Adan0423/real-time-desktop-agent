from __future__ import annotations

import ctypes
import sys
from typing import Any


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38

# Backdrop types for Windows 11
DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2  # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
DWMSBT_TABBEDWINDOW = 4  # Mica Alt


def apply_windows_11_theme(hwnd: int, dark_mode: bool = True, rounded_corners: bool = True) -> bool:
    """Apply native Windows 11 DWM dark mode and rounded corner preferences via C/Win32 APIs."""
    if sys.platform != "win32":
        return False

    try:
        dwmapi = ctypes.windll.dwmapi
        # Enable Immersive Dark Mode
        value = ctypes.c_int(1 if dark_mode else 0)
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        # Enable Rounded Corners (DWMWCP_ROUND = 2)
        if rounded_corners:
            corner_val = ctypes.c_int(2)
            dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
                ctypes.byref(corner_val),
                ctypes.sizeof(corner_val),
            )
        return True
    except Exception:
        return False


def enable_mica_effect(hwnd: int, backdrop_type: int = DWMSBT_MAINWINDOW) -> bool:
    """Enable native Windows 11 Mica / Acrylic backdrop translucency effect on the target HWND."""
    if sys.platform != "win32":
        return False

    try:
        dwmapi = ctypes.windll.dwmapi
        backdrop_val = ctypes.c_int(backdrop_type)
        res = dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(backdrop_val),
            ctypes.sizeof(backdrop_val),
        )
        return res == 0
    except Exception:
        return False
