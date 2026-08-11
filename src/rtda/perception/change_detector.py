from __future__ import annotations

import time

from rtda.capture.frame_buffer import FrameBuffer
from rtda.models.perception import ChangeDetectionResult
from rtda.performance.metrics import ProcessingMetrics
from rtda.perception.interface import ChangeDetector


class FrameChangeProcessor:
    """Processes only fresh frame pairs from a buffer."""

    def __init__(self, detector: ChangeDetector, metrics: ProcessingMetrics | None = None) -> None:
        self._detector = detector
        self._metrics = metrics or ProcessingMetrics()
        self._last_processed_sequence: int | None = None

    @property
    def metrics(self) -> ProcessingMetrics:
        return self._metrics

    def process_buffer(self, buffer: FrameBuffer) -> ChangeDetectionResult | None:
        previous, latest = buffer.latest_pair()
        if previous is None or latest is None:
            return None
        if self._last_processed_sequence == latest.sequence:
            return None

        result = self._detector.detect(previous, latest)
        self._last_processed_sequence = latest.sequence
        self._metrics.record_change_detection(
            timestamp=time.perf_counter(),
            opencv_latency_ms=result.latency_ms,
            changed=result.changed,
            region_count=result.region_count,
            changed_ratio=result.changed_ratio,
        )
        return result
