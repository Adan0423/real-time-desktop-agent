from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

from rtda.capture.interface import CaptureConfig
from rtda.capture.windows_capture import WindowsCaptureEngine


class FakeCaptureControl:
    def __init__(self) -> None:
        self.stopped = False
        self.waited = False

    def stop(self) -> None:
        self.stopped = True

    def wait(self) -> None:
        self.waited = True


class FakeInternalCaptureControl:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakeWindowsCapture:
    control = FakeCaptureControl()
    internal_control = FakeInternalCaptureControl()

    def __init__(self, **_: Any) -> None:
        self.frame_handler = None
        self.closed_handler = None

    def event(self, handler: Any) -> Any:
        if handler.__name__ == "on_frame_arrived":
            self.frame_handler = handler
        elif handler.__name__ == "on_closed":
            self.closed_handler = handler
        return handler

    def start_free_threaded(self) -> FakeCaptureControl:
        if self.frame_handler is not None:
            self.frame_handler(object(), self.internal_control)
        return self.control


def test_wgc_stop_waits_on_free_threaded_control(monkeypatch) -> None:
    FakeWindowsCapture.control = FakeCaptureControl()
    FakeWindowsCapture.internal_control = FakeInternalCaptureControl()
    monkeypatch.setitem(sys.modules, "windows_capture", SimpleNamespace(WindowsCapture=FakeWindowsCapture))

    capture = WindowsCaptureEngine(CaptureConfig(backend="wgc", window_title="Example"))
    monkeypatch.setattr(capture, "_push_native_frame", lambda native_frame, *, source: None)

    capture.start()

    assert capture._native_control is FakeWindowsCapture.control
    assert capture._native_internal_control is FakeWindowsCapture.internal_control

    capture.stop()

    assert FakeWindowsCapture.control.stopped is True
    assert FakeWindowsCapture.control.waited is True
    assert FakeWindowsCapture.internal_control.stopped is True
