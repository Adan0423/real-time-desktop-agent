from __future__ import annotations

import ctypes
import ctypes.wintypes
import threading
import time
from dataclasses import dataclass
from typing import Callable

from rtda.events.bus import DesktopEvent, EventBus, WindowChangedEvent

# ------------------------------------------------------------------
# Win32 Event Hook Constants & Types
# ------------------------------------------------------------------

HWINEVENTHOOK = ctypes.wintypes.HANDLE
DWORD = ctypes.wintypes.DWORD
LONG = ctypes.c_long

WINEVENT_OUTOFCONTEXT = 0x0000
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_HIDE = 0x8003
EVENT_OBJECT_NAMECHANGE = 0x800C

WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    HWINEVENTHOOK,
    DWORD,
    ctypes.wintypes.HWND,
    LONG,
    LONG,
    DWORD,
    DWORD,
)


@dataclass(frozen=True, slots=True)
class UIObjectChangedEvent(DesktopEvent):
    def __init__(self, hwnd: int, event_type: str) -> None:
        super().__init__(
            name="ui_object_changed",
            data={"hwnd": hwnd, "event_type": event_type},
        )


class Win32EventListener:
    """Listens to native Windows WinEvents in real time using user32.SetWinEventHook.

    Emits WinEvent notifications directly to the RTDA EventBus without polling.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus or EventBus()
        self._hook: HWINEVENTHOOK | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._callback_ref: WinEventProcType | None = None

    def start(self) -> None:
        """Start the WinEvent listener background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the WinEvent listener."""
        self._running = False

    def _run_loop(self) -> None:
        user32 = ctypes.windll.user32

        def win_event_proc(
            hWinEventHook: HWINEVENTHOOK,
            event: DWORD,
            hwnd: ctypes.wintypes.HWND,
            idObject: LONG,
            idChild: LONG,
            dwEventThread: DWORD,
            dwmsEventTime: DWORD,
        ) -> None:
            if not self._running:
                return

            event_val = event
            if event_val == EVENT_SYSTEM_FOREGROUND:
                # Foreground window changed
                try:
                    length = user32.GetWindowTextLengthW(hwnd)
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value or None
                    self.event_bus.publish(
                        WindowChangedEvent(previous_window=None, new_window=title)
                    )
                except Exception:
                    pass
            elif event_val in (EVENT_OBJECT_SHOW, EVENT_OBJECT_NAMECHANGE):
                self.event_bus.publish(
                    UIObjectChangedEvent(hwnd=int(hwnd or 0), event_type=str(event_val))
                )

        self._callback_ref = WinEventProcType(win_event_proc)

        self._hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_OBJECT_NAMECHANGE,
            None,
            self._callback_ref,
            0,
            0,
            WINEVENT_OUTOFCONTEXT,
        )

        # Message loop required for OutOfContext WinEvent hooks
        msg = ctypes.wintypes.MSG()
        while self._running:
            if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):  # PM_REMOVE
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.01)

        if self._hook:
            user32.UnhookWinEvent(self._hook)
            self._hook = None
