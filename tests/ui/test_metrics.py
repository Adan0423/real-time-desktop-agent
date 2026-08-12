from __future__ import annotations

from rtda.performance.metrics import CaptureMetrics
from rtda.performance.metrics import ProcessingMetrics


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


def test_processing_metrics_records_change_detection() -> None:
    metrics = ProcessingMetrics(window_s=10)
    metrics.reset()

    metrics.record_change_detection(
        timestamp=1.0,
        opencv_latency_ms=4.5,
        changed=True,
        region_count=2,
        changed_ratio=0.1,
    )
    metrics.record_change_detection(
        timestamp=1.2,
        opencv_latency_ms=2.0,
        changed=False,
        region_count=0,
        changed_ratio=0.0,
    )

    snapshot = metrics.snapshot()

    assert snapshot.processing_fps > 0
    assert snapshot.opencv_latency_ms == 2.0
    assert snapshot.frames_processed == 2
    assert snapshot.changed_frames == 1
    assert snapshot.latest_changed_regions == 0
    assert snapshot.ocr_latency_ms is None
    assert snapshot.vision_ai_latency_ms is None
    assert snapshot.action_latency_ms is None


def test_processing_metrics_records_uia_snapshot() -> None:
    metrics = ProcessingMetrics(window_s=10)

    metrics.record_uia_snapshot(timestamp=1.0, uia_latency_ms=8.5, element_count=12)
    snapshot = metrics.snapshot()

    assert snapshot.uia_latency_ms == 8.5
    assert snapshot.uia_snapshots == 1
    assert snapshot.latest_uia_elements == 12


def test_processing_metrics_records_ocr_vision_and_action() -> None:
    metrics = ProcessingMetrics(window_s=10)

    metrics.record_ocr(timestamp=1.0, ocr_latency_ms=30.0, element_count=3)
    metrics.record_vision_ai(timestamp=1.1, latency_ms=80.0)
    metrics.record_action(timestamp=1.2, action_latency_ms=12.0)
    snapshot = metrics.snapshot()

    assert snapshot.ocr_runs == 1
    assert snapshot.latest_ocr_elements == 3
    assert snapshot.vision_ai_calls == 1
    assert snapshot.actions_executed == 1
    assert snapshot.ocr_latency_ms == 30.0
    assert snapshot.vision_ai_latency_ms == 80.0
    assert snapshot.action_latency_ms == 12.0
