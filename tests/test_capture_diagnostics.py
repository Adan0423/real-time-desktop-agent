from __future__ import annotations

import time

import numpy as np

from rtda.capture.diagnostics import monitors_to_dict, run_capture_diagnostic
from rtda.capture.frame import Frame
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo, ScreenCapture


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
    assert result.latest_frame["width"] == 100


def test_monitors_to_dict_includes_label_and_dimensions() -> None:
    monitors = [MonitorInfo(0, 123, 0, 0, 100, 80, True, "DISPLAY1")]

    payload = monitors_to_dict(monitors)

    assert payload[0]["width"] == 100
    assert payload[0]["height"] == 80
    assert "primary" in payload[0]["label"]
