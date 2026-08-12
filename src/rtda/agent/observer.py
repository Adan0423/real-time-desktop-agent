from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from dataclasses import dataclass

from rtda.models.state import UIState
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector


def _get_foreground_window_title() -> str | None:
    """Return the title of the foreground window using ctypes (no extra deps)."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return None
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or None
    except Exception:
        return None


def _get_process_name_for_hwnd(hwnd: int) -> str | None:
    """Return the process name (application) for a given HWND."""
    try:
        import ctypes.wintypes as wt

        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = pid.value
        if not process_id:
            return None

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, process_id
        )
        if not handle:
            return None
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.wintypes.DWORD(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                path = buf.value
                return path.rsplit("\\", 1)[-1] if path else None
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return None
    return None


@dataclass
class AgentObserver:
    """Observes the current desktop state using Windows APIs.

    On each call to ``observe()``:
    1. Detects the foreground window title via ctypes.
    2. Takes a UIA snapshot of that window (or the full desktop if not found).
    3. Converts UIAElements to PerceptionElements.
    4. Returns a fully populated UIState.
    """

    uia_config: UIAConfig | None = None
    _inspector: WindowsUIAutomationInspector | None = None

    def __post_init__(self) -> None:
        self._inspector = WindowsUIAutomationInspector(self.uia_config or UIAConfig())

    def observe(self, *, window_title: str | None = None) -> UIState:
        """Return a UIState populated from the current foreground window."""
        started = time.perf_counter()

        # 1. Detect foreground window
        focused_window = window_title or _get_foreground_window_title()

        # 2. Detect application name
        application: str | None = None
        if focused_window is None:
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                application = _get_process_name_for_hwnd(hwnd)
            except Exception:
                pass

        # 3. Take UIA snapshot of the active window
        assert self._inspector is not None
        snapshot = self._inspector.snapshot(window_title=focused_window)

        # 4. Convert UIA elements to PerceptionElements
        elements = snapshot.to_perception_elements()

        # 5. Try to get application name from snapshot root
        if application is None and snapshot.root is not None and snapshot.root.process_id:
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                application = _get_process_name_for_hwnd(hwnd)
            except Exception:
                pass

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _ = elapsed_ms  # available for telemetry if needed

        return UIState(
            application=application,
            window=focused_window,
            focused_window=focused_window,
            elements=elements,
            uia_snapshot=snapshot,
        )

    def observe_summary(self, *, window_title: str | None = None) -> dict:
        """Return a JSON-serialisable summary of the current observation."""
        state = self.observe(window_title=window_title)
        snap = state.uia_snapshot
        return {
            "focused_window": state.focused_window,
            "application": state.application,
            "element_count": len(state.elements),
            "uia_latency_ms": snap.latency_ms if snap else None,
            "uia_truncated": snap.truncated if snap else None,
            "uia_errors": list(snap.errors) if snap else [],
            "elements": [
                {
                    "type": el.type,
                    "text": el.text,
                    "bbox": el.bbox.to_tuple() if el.bbox else None,
                    "confidence": el.confidence,
                    "source": el.source,
                }
                for el in state.elements[:30]  # limit for readability
            ],
        }
