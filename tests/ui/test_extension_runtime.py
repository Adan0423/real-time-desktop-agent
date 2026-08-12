from __future__ import annotations

import numpy as np

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.complement import runtime as runtime_module
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.extension import RTDAExtensionRuntime
from rtda.models.actions import ActionStatus
from rtda.models.perception import BoundingBox


class FakeCaptureEngine:
    instances: list["FakeCaptureEngine"] = []

    def __init__(self, config: CaptureConfig | None = None) -> None:
        self.config = config or CaptureConfig()
        self.buffer = FrameBuffer(max_size=self.config.max_buffer_size)
        self.started = False
        self.stopped = False
        self.paused = False
        self.latest = Frame(
            timestamp=10.0,
            source_timestamp=9.995,
            width=32,
            height=32,
            data=np.zeros((32, 32, 4), dtype=np.uint8),
            sequence=1,
        )
        self.buffer.push(self.latest)
        FakeCaptureEngine.instances.append(self)

    def list_monitors(self) -> list[MonitorInfo]:
        return [
            MonitorInfo(
                index=0,
                handle=100,
                left=0,
                top=0,
                right=1920,
                bottom=1080,
                primary=True,
                device_name="DISPLAY1",
            )
        ]

    def start(self) -> None:
        self.started = True
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True
        self.started = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def latest_frame(self) -> Frame | None:
        return self.latest

    def metrics(self) -> CaptureStats:
        return CaptureStats(
            capture_fps=60.0 if self.started else 0.0,
            capture_latency_ms=5.0,
            frames_captured=1,
            buffer_dropped_frames=0,
            estimated_missed_frames=0,
            backend_errors=0,
            uptime_s=1.0,
            latest_width=2,
            latest_height=2,
        )


def test_complement_runtime_wraps_capture_lifecycle(monkeypatch) -> None:
    FakeCaptureEngine.instances = []
    monkeypatch.setattr(runtime_module, "WindowsCaptureEngine", FakeCaptureEngine)

    runtime = runtime_module.RTDAComplementRuntime(CaptureConfig(target_fps=30))

    assert runtime.running is False
    assert runtime.paused is False
    assert runtime.list_monitors()[0].label == "0: DISPLAY1 1920x1080 (primary)"

    runtime.start_capture(CaptureConfig(target_fps=60, max_buffer_size=4))

    assert runtime.running is True
    assert runtime.paused is False
    assert FakeCaptureEngine.instances[-1].started is True
    assert runtime.latest_frame() is FakeCaptureEngine.instances[-1].latest
    assert runtime.metrics().capture_fps == 60.0
    assert runtime.buffer.max_size == 4

    runtime.pause_capture()
    assert runtime.paused is True
    assert FakeCaptureEngine.instances[-1].paused is True

    runtime.resume_capture()
    assert runtime.paused is False
    assert FakeCaptureEngine.instances[-1].paused is False

    runtime.stop_capture()
    assert runtime.running is False
    assert runtime.paused is False
    assert FakeCaptureEngine.instances[-1].stopped is True


def test_start_capture_replaces_previous_capture(monkeypatch) -> None:
    FakeCaptureEngine.instances = []
    monkeypatch.setattr(runtime_module, "WindowsCaptureEngine", FakeCaptureEngine)

    runtime = runtime_module.RTDAComplementRuntime(RTDAComplementConfig(dry_run_actions=False))
    first = FakeCaptureEngine.instances[-1]

    runtime.start_capture(CaptureConfig(target_fps=30))

    assert first.stopped is True
    assert runtime.config.target_fps == 30
    assert runtime.settings.dry_run_actions is False
    assert FakeCaptureEngine.instances[-1] is not first
    assert FakeCaptureEngine.instances[-1].started is True


def test_extension_runtime_import_path_remains_compatible() -> None:
    assert issubclass(RTDAExtensionRuntime, RTDAComplementRuntime)


def test_complement_runtime_exposes_mouse_keyboard_and_vision(monkeypatch) -> None:
    FakeCaptureEngine.instances = []
    monkeypatch.setattr(runtime_module, "WindowsCaptureEngine", FakeCaptureEngine)

    runtime = runtime_module.RTDAComplementRuntime(
        RTDAComplementConfig(capture=CaptureConfig(max_buffer_size=4), dry_run_actions=True)
    )
    runtime.start_capture()
    runtime.buffer.push(
        Frame(
            timestamp=10.1,
            source_timestamp=10.095,
            width=32,
            height=32,
            data=np.full((32, 32, 4), 255, dtype=np.uint8),
            sequence=2,
        )
    )

    click = runtime.click(bbox=BoundingBox(0, 0, 2, 2))
    hotkey = runtime.hotkey("ctrl", "l")
    change = runtime.detect_changes()

    assert click.status == ActionStatus.DRY_RUN
    assert click.metadata["x"] == 1
    assert hotkey.status == ActionStatus.DRY_RUN
    assert change is not None
    assert change.changed is True


def test_complement_border_is_explicit_capability(monkeypatch) -> None:
    FakeCaptureEngine.instances = []
    monkeypatch.setattr(runtime_module, "WindowsCaptureEngine", FakeCaptureEngine)

    class FakeBorder:
        def __init__(self) -> None:
            self.rect = None
            self.hidden = False

        def show_rect(self, rect) -> None:
            self.rect = rect

        def hide(self) -> None:
            self.hidden = True

    border = FakeBorder()
    runtime = runtime_module.RTDAComplementRuntime(
        RTDAComplementConfig(capture=CaptureConfig(), enable_border=True)
    )
    monkeypatch.setattr(runtime, "_create_border_overlay", lambda: border)

    runtime.start_capture()
    rect = runtime.refresh_border()

    assert rect is not None
    assert border.rect == rect
    assert rect.width == 1920
    assert rect.height == 1080

    runtime.stop_capture()
    assert border.hidden is True
