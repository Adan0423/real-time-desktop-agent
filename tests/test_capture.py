from __future__ import annotations

import sys
import time
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from rtda.capture.diagnostics import monitors_to_dict, run_capture_diagnostic
from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import MAX_CAPTURE_BUFFER_SIZE, CaptureConfig, CaptureStats, MonitorInfo, ScreenCapture
from rtda.capture.region import Region
from rtda.capture.shared_memory import SharedMemoryFrameBuffer
from rtda.capture.windows_capture import WindowsCaptureEngine


class FakeCapture(ScreenCapture):
    def __init__(self) -> None:
        self.started = False
        self.paused = False
        self.stopped = False
        self.frame: Frame | None = None
        self.frames = 0

    def list_monitors(self) -> list[MonitorInfo]:
        return [MonitorInfo(0, 123, 0, 0, 100, 80, True, "DISPLAY1")]

    def start(self) -> None:
        self.started = True
        self.frames = 1
        self.frame = Frame(
            timestamp=time.perf_counter(),
            width=100,
            height=80,
            data=np.zeros((80, 100, 4), dtype=np.uint8),
            sequence=1,
            source_timestamp=time.perf_counter(),
        )

    def stop(self) -> None:
        self.stopped = True
        self.frame = None

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def latest_frame(self) -> Frame | None:
        return self.frame

    def get_fps(self) -> float:
        return 1.0

    def get_latency(self) -> float | None:
        return 0.0

    def metrics(self) -> CaptureStats:
        return CaptureStats(
            capture_fps=1.0,
            capture_latency_ms=0.0,
            frames_captured=self.frames,
            buffer_dropped_frames=0,
            estimated_missed_frames=0,
            backend_errors=0,
            uptime_s=0.1,
            latest_width=100,
            latest_height=80,
        )


def make_frame(sequence: int, width: int = 4, height: int = 3) -> Frame:
    data = np.arange(width * height * 4, dtype=np.uint8).reshape((height, width, 4))
    return Frame(timestamp=float(sequence), width=width, height=height, data=data, sequence=sequence)


# ── Diagnostics Tests ───────────────────────────────────────────────────────

def test_capture_diagnostic_passes_with_fake_capture() -> None:
    capture = FakeCapture()
    result = run_capture_diagnostic(
        capture,
        config=CaptureConfig(target_fps=30),
        duration_s=0.03,
        pause_s=0.001,
        poll_interval_s=0.005,
    )
    assert result.passed is True
    assert result.checks["capture_started"] is True
    assert result.checks["pause_resume_called"] is True
    assert result.checks["stopped_cleanly"] is True
    assert result.checks["latest_frame_available"] is True
    assert result.latest_frame is None


def test_monitors_to_dict_includes_label_and_dimensions() -> None:
    monitors = [MonitorInfo(0, 123, 0, 0, 100, 80, True, "DISPLAY1")]
    payload = monitors_to_dict(monitors)
    assert payload[0]["width"] == 100
    assert payload[0]["height"] == 80
    assert "primary" in payload[0]["label"]


# ── Frame Buffer Tests ──────────────────────────────────────────────────────

def test_frame_buffer_keeps_latest_and_previous() -> None:
    buffer = FrameBuffer(max_size=2)
    buffer.push(make_frame(1))
    buffer.push(make_frame(2))
    buffer.push(make_frame(3))

    assert len(buffer) == 2
    assert buffer.dropped_frames == 1
    assert buffer.latest().sequence == 3
    assert buffer.previous().sequence == 2


def test_frame_region_returns_expected_shape() -> None:
    frame = make_frame(1, width=5, height=4)
    region = frame.get_region(Region(1, 1, 4, 3))

    assert region.width == 3
    assert region.height == 2
    assert region.data.shape == (2, 3, 4)
    assert region.metadata["parent_sequence"] == 1


def test_buffer_get_region_uses_latest_frame() -> None:
    buffer = FrameBuffer(max_size=3)
    buffer.push(make_frame(1))
    buffer.push(make_frame(2, width=6, height=5))

    region = buffer.get_region(Region(0, 0, 2, 2))

    assert region is not None
    assert region.sequence == 2
    assert region.data.shape == (2, 2, 4)


def test_latest_pair_is_a_consistent_snapshot() -> None:
    buffer = FrameBuffer(max_size=3)

    assert buffer.latest_pair() == (None, None)
    buffer.push(make_frame(1))
    assert buffer.latest_pair()[0] is None
    buffer.push(make_frame(2))

    previous, latest = buffer.latest_pair()

    assert previous.sequence == 1
    assert latest.sequence == 2


def test_capture_config_defaults_to_minimal_live_buffer() -> None:
    config = CaptureConfig()
    assert config.max_buffer_size == 2


def test_capture_config_rejects_unbounded_frame_retention() -> None:
    too_many_frames = MAX_CAPTURE_BUFFER_SIZE + 1
    try:
        CaptureConfig(max_buffer_size=too_many_frames)
    except ValueError as exc:
        assert "max_buffer_size" in str(exc)
    else:
        raise AssertionError("expected max_buffer_size validation to reject unbounded retention")


# ── Region Tests ─────────────────────────────────────────────────────────────

def test_region_validates_dimensions() -> None:
    with pytest.raises(ValueError):
        Region(10, 0, 10, 20)
    with pytest.raises(ValueError):
        Region(0, 5, 10, 5)


def test_region_clamps_to_frame_size() -> None:
    region = Region(5, 5, 20, 20)
    clamped = region.clamp(12, 10)
    assert clamped.to_tuple() == (5, 5, 12, 10)


# ── Shared Memory Tests ─────────────────────────────────────────────────────

def test_shared_memory_frame_buffer_write_read() -> None:
    shm_buf = SharedMemoryFrameBuffer(name="test_rtda_shm_buffer", size_bytes=100 * 100 * 4)
    try:
        shm_buf.create()

        original_data = np.full((100, 100, 4), fill_value=128, dtype=np.uint8)
        original_data[10, 10] = [255, 0, 0, 255]

        shm_buf.write_frame(original_data)
        read_data = shm_buf.read_frame(width=100, height=100, channels=4)

        assert read_data.shape == (100, 100, 4)
        assert np.array_equal(read_data[10, 10], [255, 0, 0, 255])
        assert np.array_equal(read_data[0, 0], [128, 128, 128, 128])
    finally:
        shm_buf.close()


# ── Windows Capture Lifecycle Tests ─────────────────────────────────────────

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


def test_stop_clears_retained_frames() -> None:
    capture = WindowsCaptureEngine(CaptureConfig())
    capture.buffer.push(
        Frame(
            timestamp=1.0,
            width=2,
            height=2,
            data=np.zeros((2, 2, 4), dtype=np.uint8),
            sequence=1,
        )
    )

    capture.stop()

    assert capture.latest_frame() is None
    assert len(capture.buffer) == 0
