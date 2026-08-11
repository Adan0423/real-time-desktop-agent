from __future__ import annotations

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.capture.windows_capture import WindowsCaptureEngine


class RTDAExtensionRuntime:
    """In-process facade for the RTDA extension capabilities.

    The desktop app consumes this runtime just like an external AI host consumes
    the MCP tools: the advanced desktop capabilities live behind this boundary.
    """

    def __init__(self, config: CaptureConfig | None = None) -> None:
        self._config = config or CaptureConfig()
        self._capture = WindowsCaptureEngine(self._config)
        self._running = False
        self._paused = False

    @property
    def config(self) -> CaptureConfig:
        return self._config

    @property
    def buffer(self) -> FrameBuffer:
        return self._capture.buffer

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    def list_monitors(self) -> list[MonitorInfo]:
        return self._capture.list_monitors()

    def start_capture(self, config: CaptureConfig | None = None) -> None:
        self.stop_capture()
        if config is not None:
            self._config = config
        self._capture = WindowsCaptureEngine(self._config)
        self._capture.start()
        self._running = True
        self._paused = False

    def stop_capture(self) -> None:
        self._capture.stop()
        self._running = False
        self._paused = False

    def pause_capture(self) -> None:
        if not self._running:
            return
        self._capture.pause()
        self._paused = True

    def resume_capture(self) -> None:
        if not self._running:
            return
        self._capture.resume()
        self._paused = False

    def latest_frame(self) -> Frame | None:
        return self._capture.latest_frame()

    def metrics(self) -> CaptureStats:
        return self._capture.metrics()
