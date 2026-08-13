from __future__ import annotations

import ctypes
from pathlib import Path
import sys

# Load compiled C/C++ native DLL library
_DLL_PATH = Path(__file__).parent / "win32_helper.dll"
_NATIVE_DLL: ctypes.CDLL | None = None

if _DLL_PATH.exists():
    try:
        _NATIVE_DLL = ctypes.CDLL(str(_DLL_PATH))
        _NATIVE_DLL.native_get_high_res_time_ms.restype = ctypes.c_double
        _NATIVE_DLL.native_apply_win11_theme.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        _NATIVE_DLL.native_enable_mica.argtypes = [ctypes.c_void_p, ctypes.c_int]
    except Exception:
        _NATIVE_DLL = None


def get_native_high_res_time_ms() -> float:
    """Return microsecond precision timestamp from native C DLL."""
    if _NATIVE_DLL and hasattr(_NATIVE_DLL, "native_get_high_res_time_ms"):
        return float(_NATIVE_DLL.native_get_high_res_time_ms())
    import time
    return time.time() * 1000.0


def apply_windows_11_theme(hwnd: int, dark_mode: bool = True, rounded_corners: bool = True) -> bool:
    """Apply native Windows 11 DWM dark mode via compiled C DLL or fallback to Win32 ctypes."""
    if sys.platform != "win32":
        return False

    if _NATIVE_DLL and hasattr(_NATIVE_DLL, "native_apply_win11_theme"):
        return bool(_NATIVE_DLL.native_apply_win11_theme(ctypes.c_void_p(hwnd), 1 if dark_mode else 0, 1 if rounded_corners else 0))

    try:
        dwmapi = ctypes.windll.dwmapi
        value = ctypes.c_int(1 if dark_mode else 0)
        dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 20, ctypes.byref(value), ctypes.sizeof(value))
        if rounded_corners:
            corner_val = ctypes.c_int(2)
            dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 33, ctypes.byref(corner_val), ctypes.sizeof(corner_val))
        return True
    except Exception:
        return False


def enable_mica_effect(hwnd: int, backdrop_type: int = 2) -> bool:
    """Enable native Windows 11 Mica / Acrylic effect via compiled C DLL."""
    if sys.platform != "win32":
        return False

    if _NATIVE_DLL and hasattr(_NATIVE_DLL, "native_enable_mica"):
        return bool(_NATIVE_DLL.native_enable_mica(ctypes.c_void_p(hwnd), backdrop_type))

    try:
        dwmapi = ctypes.windll.dwmapi
        backdrop_val = ctypes.c_int(backdrop_type)
        res = dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 38, ctypes.byref(backdrop_val), ctypes.sizeof(backdrop_val))
        return res == 0
    except Exception:
        return False
