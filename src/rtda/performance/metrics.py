from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from rtda.capture.interface import CaptureStats


@dataclass(frozen=True, slots=True)
class ProcessingStats:
    processing_fps: float
    opencv_latency_ms: float | None
    uia_latency_ms: float | None
    ocr_latency_ms: float | None
    vision_ai_latency_ms: float | None
    action_latency_ms: float | None
    frames_processed: int
    changed_frames: int
    latest_changed_regions: int
    latest_changed_ratio: float
    uia_snapshots: int
    latest_uia_elements: int
    ocr_runs: int
    latest_ocr_elements: int
    vision_ai_calls: int
    actions_executed: int
    uptime_s: float


class CaptureMetrics:
    """Rolling capture metrics for a single session."""

    def __init__(self, *, target_fps: int, window_s: float = 2.0) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be positive")
        self._target_fps = target_fps
        self._window_s = window_s
        self._lock = Lock()
        self._frame_times: deque[float] = deque()
        self._start_time: float | None = None
        self._last_frame_time: float | None = None
        self._latest_latency_ms: float | None = None
        self._frames_captured = 0
        self._buffer_dropped_frames = 0
        self._estimated_missed_frames = 0
        self._backend_errors = 0
        self._latest_width: int | None = None
        self._latest_height: int | None = None

    def reset(self) -> None:
        with self._lock:
            self._frame_times.clear()
            self._start_time = time.perf_counter()
            self._last_frame_time = None
            self._latest_latency_ms = None
            self._frames_captured = 0
            self._buffer_dropped_frames = 0
            self._estimated_missed_frames = 0
            self._backend_errors = 0
            self._latest_width = None
            self._latest_height = None

    def record_frame(
        self,
        *,
        timestamp: float,
        latency_ms: float | None,
        width: int,
        height: int,
        buffer_dropped: int = 0,
    ) -> None:
        expected_interval = 1.0 / self._target_fps
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            if self._last_frame_time is not None:
                gap = timestamp - self._last_frame_time
                if gap > expected_interval * 1.5:
                    self._estimated_missed_frames += max(0, round(gap / expected_interval) - 1)
            self._last_frame_time = timestamp
            self._latest_latency_ms = latency_ms
            self._frames_captured += 1
            self._buffer_dropped_frames += buffer_dropped
            self._latest_width = width
            self._latest_height = height
            self._frame_times.append(timestamp)
            cutoff = timestamp - self._window_s
            while self._frame_times and self._frame_times[0] < cutoff:
                self._frame_times.popleft()

    def record_error(self) -> None:
        with self._lock:
            self._backend_errors += 1

    def fps(self) -> float:
        with self._lock:
            return self._fps_unlocked()

    def latency(self) -> float | None:
        with self._lock:
            return self._latest_latency_ms

    def snapshot(self) -> CaptureStats:
        with self._lock:
            now = time.perf_counter()
            uptime = 0.0 if self._start_time is None else now - self._start_time
            return CaptureStats(
                capture_fps=self._fps_unlocked(),
                capture_latency_ms=self._latest_latency_ms,
                frames_captured=self._frames_captured,
                buffer_dropped_frames=self._buffer_dropped_frames,
                estimated_missed_frames=self._estimated_missed_frames,
                backend_errors=self._backend_errors,
                uptime_s=uptime,
                latest_width=self._latest_width,
                latest_height=self._latest_height,
            )

    def _fps_unlocked(self) -> float:
        if len(self._frame_times) < 2:
            return 0.0
        elapsed = self._frame_times[-1] - self._frame_times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._frame_times) - 1) / elapsed


class ProcessingMetrics:
    """Rolling metrics for local perception work."""

    def __init__(self, *, window_s: float = 2.0) -> None:
        self._window_s = window_s
        self._lock = Lock()
        self._process_times: deque[float] = deque()
        self._start_time: float | None = None
        self._latest_opencv_latency_ms: float | None = None
        self._latest_uia_latency_ms: float | None = None
        self._latest_ocr_latency_ms: float | None = None
        self._latest_vision_ai_latency_ms: float | None = None
        self._latest_action_latency_ms: float | None = None
        self._frames_processed = 0
        self._changed_frames = 0
        self._latest_changed_regions = 0
        self._latest_changed_ratio = 0.0
        self._uia_snapshots = 0
        self._latest_uia_elements = 0
        self._ocr_runs = 0
        self._latest_ocr_elements = 0
        self._vision_ai_calls = 0
        self._actions_executed = 0

    def reset(self) -> None:
        with self._lock:
            self._process_times.clear()
            self._start_time = time.perf_counter()
            self._latest_opencv_latency_ms = None
            self._latest_uia_latency_ms = None
            self._latest_ocr_latency_ms = None
            self._latest_vision_ai_latency_ms = None
            self._latest_action_latency_ms = None
            self._frames_processed = 0
            self._changed_frames = 0
            self._latest_changed_regions = 0
            self._latest_changed_ratio = 0.0
            self._uia_snapshots = 0
            self._latest_uia_elements = 0
            self._ocr_runs = 0
            self._latest_ocr_elements = 0
            self._vision_ai_calls = 0
            self._actions_executed = 0

    def record_change_detection(
        self,
        *,
        timestamp: float,
        opencv_latency_ms: float,
        changed: bool,
        region_count: int,
        changed_ratio: float,
    ) -> None:
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            self._latest_opencv_latency_ms = opencv_latency_ms
            self._frames_processed += 1
            if changed:
                self._changed_frames += 1
            self._latest_changed_regions = region_count
            self._latest_changed_ratio = changed_ratio
            self._process_times.append(timestamp)
            cutoff = timestamp - self._window_s
            while self._process_times and self._process_times[0] < cutoff:
                self._process_times.popleft()

    def record_uia_snapshot(self, *, timestamp: float, uia_latency_ms: float, element_count: int) -> None:
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            self._latest_uia_latency_ms = uia_latency_ms
            self._uia_snapshots += 1
            self._latest_uia_elements = element_count

    def record_ocr(self, *, timestamp: float, ocr_latency_ms: float, element_count: int) -> None:
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            self._latest_ocr_latency_ms = ocr_latency_ms
            self._ocr_runs += 1
            self._latest_ocr_elements = element_count

    def record_vision_ai(self, *, timestamp: float, latency_ms: float) -> None:
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            self._latest_vision_ai_latency_ms = latency_ms
            self._vision_ai_calls += 1

    def record_action(self, *, timestamp: float, action_latency_ms: float) -> None:
        with self._lock:
            if self._start_time is None:
                self._start_time = timestamp
            self._latest_action_latency_ms = action_latency_ms
            self._actions_executed += 1

    def snapshot(self) -> ProcessingStats:
        with self._lock:
            now = time.perf_counter()
            uptime = 0.0 if self._start_time is None else now - self._start_time
            return ProcessingStats(
                processing_fps=self._fps_unlocked(),
                opencv_latency_ms=self._latest_opencv_latency_ms,
                uia_latency_ms=self._latest_uia_latency_ms,
                ocr_latency_ms=self._latest_ocr_latency_ms,
                vision_ai_latency_ms=self._latest_vision_ai_latency_ms,
                action_latency_ms=self._latest_action_latency_ms,
                frames_processed=self._frames_processed,
                changed_frames=self._changed_frames,
                latest_changed_regions=self._latest_changed_regions,
                latest_changed_ratio=self._latest_changed_ratio,
                uia_snapshots=self._uia_snapshots,
                latest_uia_elements=self._latest_uia_elements,
                ocr_runs=self._ocr_runs,
                latest_ocr_elements=self._latest_ocr_elements,
                vision_ai_calls=self._vision_ai_calls,
                actions_executed=self._actions_executed,
                uptime_s=uptime,
            )

    def _fps_unlocked(self) -> float:
        if len(self._process_times) < 2:
            return 0.0
        elapsed = self._process_times[-1] - self._process_times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._process_times) - 1) / elapsed
