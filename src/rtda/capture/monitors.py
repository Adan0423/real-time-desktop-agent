from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from rtda.capture.interface import MonitorInfo


class _MonitorInfoExW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


def _handle_to_int(handle: object) -> int:
    value = getattr(handle, "value", handle)
    return int(value or 0)


def list_windows_monitors() -> list[MonitorInfo]:
    """Return monitors using Win32 APIs without importing a capture backend."""

    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    monitors: list[MonitorInfo] = []
    monitor_enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )

    def callback(
        hmonitor: wintypes.HMONITOR,
        _hdc: wintypes.HDC,
        _rect: ctypes.POINTER(wintypes.RECT),
        _data: wintypes.LPARAM,
    ) -> bool:
        info = _MonitorInfoExW()
        info.cbSize = ctypes.sizeof(_MonitorInfoExW)
        if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return True
        monitors.append(
            MonitorInfo(
                index=len(monitors),
                handle=_handle_to_int(hmonitor),
                left=info.rcMonitor.left,
                top=info.rcMonitor.top,
                right=info.rcMonitor.right,
                bottom=info.rcMonitor.bottom,
                primary=bool(info.dwFlags & 1),
                device_name=info.szDevice,
            )
        )
        return True

    if not user32.EnumDisplayMonitors(0, 0, monitor_enum_proc(callback), 0):
        raise OSError("EnumDisplayMonitors failed")
    return monitors
