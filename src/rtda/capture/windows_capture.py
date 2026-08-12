from __future__ import annotations

import inspect
import threading
import time
from dataclasses import asdict
from typing import Any

import numpy as np

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo, ScreenCapture
from rtda.capture.monitors import list_windows_monitors
from rtda.performance.metrics import CaptureMetrics


class WindowsCaptureEngine(ScreenCapture):
    """Windows capture backend using the optional `windows-capture` package."""

    def __init__(self, config: CaptureConfig | None = None) -> None:
        self.config = config or CaptureConfig()
        self.buffer = FrameBuffer(max_size=self.config.max_buffer_size)
        self._metrics = CaptureMetrics(target_fps=self.config.target_fps)
        self._running = threading.Event()
        self._paused = threading.Event()
        self._thread: threading.Thread | None = None
        self._sequence = 0
        self._native_capture: Any = None
        self._native_control: Any = None
        self._native_internal_control: Any = None
        self._native_session: Any = None
        self._lock = threading.Lock()

    def list_monitors(self) -> list[MonitorInfo]:
        return list_windows_monitors()

    def start(self) -> None:
        with self._lock:
            if self._running.is_set():
                return
            self.buffer.clear()
            self._metrics.reset()
            self._running.set()
            self._paused.clear()
            self._sequence = 0
            if self.config.backend == "wgc":
                self._start_wgc_locked()
            else:
                self._start_dxgi_locked()

    def stop(self) -> None:
        self._running.clear()
        control = self._native_control
        internal_control = self._native_internal_control
        if control is not None and hasattr(control, "stop"):
            try:
                control.stop()
            except Exception:
                self._metrics.record_error()
        if (
            internal_control is not None
            and internal_control is not control
            and hasattr(internal_control, "stop")
        ):
            try:
                internal_control.stop()
            except Exception:
                self._metrics.record_error()
        capture = self._native_capture
        if capture is not None and hasattr(capture, "stop"):
            try:
                capture.stop()
            except Exception:
                self._metrics.record_error()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        if control is not None and hasattr(control, "wait"):
            try:
                control.wait()
            except Exception:
                self._metrics.record_error()
        self._thread = None
        self._native_capture = None
        self._native_control = None
        self._native_internal_control = None
        self._native_session = None
        self.buffer.clear()

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def latest_frame(self) -> Frame | None:
        return self.buffer.latest()

    def get_fps(self) -> float:
        return self._metrics.fps()

    def get_latency(self) -> float | None:
        return self._metrics.latency()

    def metrics(self) -> CaptureStats:
        return self._metrics.snapshot()

    def _start_wgc_locked(self) -> None:
        try:
            from windows_capture import WindowsCapture
        except ImportError as exc:
            raise RuntimeError(
                "Missing optional dependency 'windows-capture'. "
                "Install with: python -m pip install -e .[capture]"
            ) from exc

        kwargs: dict[str, Any] = {
            "cursor_capture": self.config.capture_cursor,
            "draw_border": self.config.draw_border,
            "window_name": self.config.window_title,
        }
        if self.config.window_title is None:
            # windows-capture WGC monitor selection is one-based.
            kwargs["monitor_index"] = self.config.monitor_index + 1
        else:
            kwargs["monitor_index"] = None
        interval_ms = max(1, round(1000 / self.config.target_fps))
        if "minimum_update_interval" in inspect.signature(WindowsCapture).parameters:
            kwargs["minimum_update_interval"] = interval_ms

        capture = WindowsCapture(**kwargs)

        @capture.event
        def on_frame_arrived(native_frame: Any, capture_control: Any) -> None:
            self._native_internal_control = capture_control
            if not self._running.is_set():
                capture_control.stop()
                return
            if self._paused.is_set():
                return
            self._push_native_frame(native_frame, source="wgc")

        @capture.event
        def on_closed() -> None:
            self._running.clear()

        self._native_capture = capture
        if hasattr(capture, "start_free_threaded"):
            self._native_control = capture.start_free_threaded()
            return

        self._thread = threading.Thread(target=capture.start, name="rtda-wgc-capture", daemon=True)
        self._thread.start()

    def _start_dxgi_locked(self) -> None:
        try:
            import windows_capture  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Missing optional dependency 'windows-capture'. "
                "Install with: python -m pip install -e .[capture]"
            ) from exc

        self._thread = threading.Thread(target=self._dxgi_loop, name="rtda-dxgi-capture", daemon=True)
        self._thread.start()

    def _dxgi_loop(self) -> None:
        from windows_capture import DxgiDuplicationSession

        # windows-capture DXGI objects are thread-affine, so create and use the
        # native session in this worker thread.
        try:
            session = DxgiDuplicationSession(monitor_index=self.config.monitor_index + 1)
        except Exception:
            self._metrics.record_error()
            self._running.clear()
            return
        timeout_ms = max(1, round(1000 / self.config.target_fps))
        interval_s = 1.0 / self.config.target_fps
        next_tick = time.perf_counter()
        try:
            while self._running.is_set():
                if self._paused.is_set():
                    time.sleep(min(0.1, interval_s))
                    next_tick = time.perf_counter()
                    continue
                try:
                    native_frame = session.acquire_frame(timeout_ms=timeout_ms)
                except RuntimeError:
                    self._metrics.record_error()
                    if hasattr(session, "recreate"):
                        session.recreate()
                    continue
                if native_frame is not None:
                    self._push_native_frame(native_frame, source="dxgi")
                next_tick += interval_s
                sleep_s = next_tick - time.perf_counter()
                if sleep_s > 0:
                    time.sleep(sleep_s)
                else:
                    next_tick = time.perf_counter()
        finally:
            if hasattr(session, "close"):
                session.close()

    def _push_native_frame(self, native_frame: Any, *, source: str) -> None:
        received_at = time.perf_counter()
        try:
            array = self._frame_to_numpy(native_frame)
        except Exception:
            self._metrics.record_error()
            return
        if self.config.region is not None:
            region = self.config.region.clamp(array.shape[1], array.shape[0])
            array = array[region.top : region.bottom, region.left : region.right, ...].copy()
        source_timestamp = self._extract_source_timestamp(native_frame, received_at)
        self._sequence += 1
        frame = Frame(
            timestamp=received_at,
            width=int(array.shape[1]),
            height=int(array.shape[0]),
            data=array,
            sequence=self._sequence,
            source_timestamp=source_timestamp,
            metadata={
                "backend": self.config.backend,
                "native_source": source,
                "config": asdict(self.config),
            },
        )
        dropped = self.buffer.push(frame)
        self._metrics.record_frame(
            timestamp=received_at,
            latency_ms=frame.latency_ms,
            width=frame.width,
            height=frame.height,
            buffer_dropped=dropped,
        )

    @staticmethod
    def _frame_to_numpy(native_frame: Any) -> np.ndarray:
        if hasattr(native_frame, "to_numpy"):
            try:
                data = native_frame.to_numpy(copy=True)
            except TypeError:
                data = native_frame.to_numpy()
        elif hasattr(native_frame, "frame_buffer"):
            data = native_frame.frame_buffer
        else:
            raise TypeError("native frame does not expose to_numpy() or frame_buffer")
        array = np.asarray(data)
        if not array.flags.c_contiguous:
            array = np.ascontiguousarray(array)
        elif not array.flags.owndata:
            array = array.copy()
        if array.ndim != 3 or array.shape[2] not in (3, 4):
            raise ValueError(f"unsupported frame shape: {array.shape}")
        return array

    @staticmethod
    def _extract_source_timestamp(native_frame: Any, fallback: float) -> float:
        raw = getattr(native_frame, "timespan", None)
        if raw is None:
            return fallback
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return fallback
        if value <= 0:
            return fallback
        # Windows Graphics Capture timespan is usually in 100 ns units.
        seconds = value / 10_000_000.0 if value > 1_000_000 else value
        if abs(fallback - seconds) > 60 * 60:
            return fallback
        return seconds
