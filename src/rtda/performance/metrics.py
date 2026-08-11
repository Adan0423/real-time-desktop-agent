from __future__ import annotations

import time
from collections import deque
from threading import Lock

from rtda.capture.interface import CaptureStats


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
