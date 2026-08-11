from __future__ import annotations

from rtda.performance.metrics import CaptureMetrics


def test_metrics_records_fps_and_drops() -> None:
    metrics = CaptureMetrics(target_fps=10, window_s=10)
    metrics.reset()
    metrics.record_frame(timestamp=1.0, latency_ms=2.0, width=100, height=50)
    metrics.record_frame(timestamp=1.1, latency_ms=3.0, width=100, height=50, buffer_dropped=1)
    snapshot = metrics.snapshot()

    assert snapshot.capture_fps > 0
    assert snapshot.capture_latency_ms == 3.0
    assert snapshot.frames_captured == 2
    assert snapshot.buffer_dropped_frames == 1
    assert snapshot.latest_width == 100
    assert snapshot.latest_height == 50


def test_metrics_estimates_missed_frames_on_long_gap() -> None:
    metrics = CaptureMetrics(target_fps=10, window_s=10)
    metrics.record_frame(timestamp=1.0, latency_ms=None, width=1, height=1)
    metrics.record_frame(timestamp=1.5, latency_ms=None, width=1, height=1)

    assert metrics.snapshot().estimated_missed_frames >= 3
